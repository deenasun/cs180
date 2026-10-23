import math
import numpy as np
import skimage as sk
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data")
OUTPUT_DIR = Path("out")


def img_to_np(input_file_path, grayscale=False):
    """Reads an image given an input_file_path, and returns a NumPy ndarray"""
    img = sk.io.imread(input_file_path)
    img = sk.img_as_float(img)

    # Convert 4-channeled RGBA images into RGB images
    if img.shape[-1] > 3:
        img = sk.color.rgba2rgb(img)

    if grayscale:
        img = sk.color.rgb2gray(img)

    return img


def save_np_as_img(output_path, arr):
    """Helper function to convert a NumPy ndarray into uint8 for saving"""
    if np.issubdtype(arr.dtype, np.floating):
        arr = (arr * 255.0).astype(np.uint8)

    sk.io.imsave(output_path, arr)

    print(f"Saved image to {output_path}")


def get_correspondences(
    img1: np.ndarray, img2: np.ndarray, num_correspondences=4
) -> tuple:
    """
    Interactive window that shows the 2 images side-by-side.
    Users can alternate clicking points in image 1 and image 2.
    """
    colors = list(mcolors.BASE_COLORS.keys())

    fig, axs = plt.subplots(1, 2, figsize=(12, 6))
    axs[0].imshow(img1)
    axs[0].set_title("Image 1")
    axs[0].gid = "image_1"  # Tag each subplot with a label

    axs[1].imshow(img2)
    axs[1].set_title("Image 2")
    axs[1].gid = "image_2"  # Tag each subplot with a label

    fig.suptitle(
        f"Please select {num_correspondences} corresponding points in each image."
    )

    im1_pts = []
    im2_pts = []
    next_axs = 0  # Require user to alternate between points in image 1 and image 2

    def on_click(event):
        nonlocal next_axs
        if event.inaxes is None:
            print("Select a point inside one of the subplots")
            return

        if event.inaxes.gid == "image_1" and next_axs == 0:
            print(f"Captured click at {event.xdata, event.ydata}")
            print(
                f"Captured click at ({event.xdata:.2f}, {event.ydata:.2f}) in image 1"
            )
            axs[0].plot(
                event.xdata,
                event.ydata,
                color=colors[len(im1_pts) % len(colors)],
                marker="o",
                markersize=6,
            )
            fig.canvas.draw()
            im1_pts.append([event.xdata, event.ydata])
            next_axs = (next_axs + 1) % 2
        elif event.inaxes.gid == "image_2" and next_axs == 1:
            print(
                f"Captured click at ({event.xdata:.2f}, {event.ydata:.2f}) in image 2"
            )
            axs[1].plot(
                event.xdata,
                event.ydata,
                color=colors[len(im2_pts) % len(colors)],
                marker="o",
                markersize=6,
            )
            fig.canvas.draw()
            im2_pts.append([event.xdata, event.ydata])
            next_axs = (next_axs + 1) % 2
        else:
            print(f"Please select a point in image {next_axs + 1} next")

        if len(im1_pts) == num_correspondences and len(im2_pts) == num_correspondences:
            # Close the figure once user has selected num_correspondences points in both images
            plt.close(fig)

    fig.canvas.mpl_connect("button_press_event", on_click)
    plt.tight_layout()
    plt.show()
    print(f"Collected {num_correspondences}")
    return np.array(im1_pts), np.array(im2_pts)


def computeH(im1_pts, im2_pts):
    """
    Args:
        im1_pts, im2_pts: (N, 2) matrices of N point correspondences between the two images
            - Each row is an (x, y) coordinate pair
            - To recover the matrix H, the inputs must contain at least 4 correspondences

    Returns:
        H: the recovered (3x3) homography matrix
    """
    #  Ah = b where h is a vector holding the 8 unknown entries of H
    # x' = (ax + by + c) / (gx + hy + 1), y' = (dx + ey + f) / (gx + hy + 1)
    # x' * (gx + hy + 1) = ax + by + c, y' * (gx + hy + 1) = dx + ey + f
    # x' = ax + by + c - x' gx - x' hy, y' = dx + ey + f - y' gx - y' hy
    # A = [[x, y, 1, 0, 0, 0, -x' * x, - x' * y ],
    #      [0, 0, 0, x, y, 1, -y' * x, - y' * y],
    #      ... ]
    #
    N = im1_pts.shape[0]
    A = np.zeros((2 * N, 8))
    b = np.zeros((2 * N,))

    for i in range(N):
        x1, y1 = im1_pts[i]
        x2, y2 = im2_pts[i]
        A[2 * i] = [x1, y1, 1, 0, 0, 0, -x2 * x1, -x2 * y1]
        A[2 * i + 1] = [0, 0, 0, x1, y1, 1, -y2 * x1, -y2 * y1]

        b[2 * i : 2 * i + 2] = [x2, y2]

    print(f"A {A}")
    print(f"b {b}")

    h, _, _, _ = np.linalg.lstsq(A, b)

    # Convert h from a column vector into a matrix
    H = np.ones((3, 3))
    for i in range(8):
        row, col = i // 3, i % 3
        H[row, col] = h[i]

    return H


def normalize(homogeneous_coord: np.ndarray):
    """Normalizes a 3D homogeneous coordinate s.t. its last component = 1"""
    if homogeneous_coord[-1] == 0 or not math.isfinite(homogeneous_coord[-1]):
        return None  # Cannot normalize homogeneous coordinate if final component is a zero or non-finite
    return homogeneous_coord / homogeneous_coord[-1]


def warpImageNearestNeighbor(im, H):
    """
    Warp im by applying the homography H.
    Compute the pixel values in the warped image using inverse warping (nearest neighbors interpolation).
    """
    print("===== Warping image using nearest neighbor inverse warping =====")
    if im.ndim == 3:
        h_in, w_in, c_in = im.shape
    else:
        h_in, w_in = im.shape

    out_top_left = H @ np.array(
        [0, 0, 1]
    )  # The pixel center of an (h, w) image's top left corner
    out_top_right = H @ np.array(
        [w_in - 1, 0, 1]
    )  # The pixel center of an (h, w) image's top right corner
    out_bottom_left = H @ np.array(
        [0, h_in - 1, 1]
    )  # The pixel center of an (h, w) image's bottom left corner
    out_bottom_right = H @ np.array(
        [w_in - 1, h_in - 1, 1]
    )  # The pixel center of an (h, w) image's bottom right corner

    out_top_left = normalize(out_top_left)
    out_top_right = normalize(out_top_right)
    out_bottom_left = normalize(out_bottom_left)
    out_bottom_right = normalize(out_bottom_right)

    # (x_min, y_min) represent the top-left corner of the warped image in the original image's space
    x_min = math.floor(
        min(out_top_left[0], out_top_right[0], out_bottom_left[0], out_bottom_right[0])
    )
    x_max = math.ceil(
        max(out_top_left[0], out_top_right[0], out_bottom_left[0], out_bottom_right[0])
    )
    y_min = math.floor(
        min(out_top_left[1], out_top_right[1], out_bottom_left[1], out_bottom_right[1])
    )
    y_max = math.ceil(
        max(out_top_left[1], out_top_right[1], out_bottom_left[1], out_bottom_right[1])
    )

    h_out = y_max - y_min + 1
    w_out = x_max - x_min + 1

    # Top-left pixel in out (matrix index (0, 0)) corresponds
    # to the pixel location (x_min, y_min) in the warped image.
    if im.ndim == 3:
        out = np.zeros((h_out, w_out, c_in))
    else:
        out = np.zeros((h_out, w_out))

    # 2D mask to mark which pixels in the output had valid source mappings.
    # Used as alpha channel later to distinguish output pixel = 0 because
    # it came from a 0 pixel in the source vs. output pixel = 0 because it
    # had no valid source mapping.
    mask = np.zeros((h_out, w_out)).astype(bool)

    H_inv = np.linalg.inv(H)

    # Iterate through pixel coordinate in the output image.
    for y in range(h_out):
        for x in range(w_out):
            # For each pixel in the output, compute which source pixels it came from
            # and "gather" colors from the source pixels.

            # First transform 0-indexed (x, y) into pixel coordinates in the warped image space.
            dest_coords = np.array([x + x_min, y + y_min, 1])
            source_coords = normalize(H_inv @ dest_coords)
            if source_coords is None:
                continue  # Skip if source_coord's final component is zero or infinity
            source_x = round(source_coords[0])
            source_y = round(source_coords[1])

            if 0 <= source_x < w_in and 0 <= source_y < h_in:
                out[y, x] = im[source_y, source_x]
                mask[y, x] = True

    return out, mask, (x_min, y_min)


def warpImageBilinear(im, H):
    """
    Warp im by applying the homography H.
    Compute the pixel values in the warped image using inverse warping (bilinear interpolation).
    """
    print("===== Warping image using bilinear interpolation inverse warping =====")
    if im.ndim == 3:
        h_in, w_in, c_in = im.shape
    else:
        h_in, w_in = im.shape

    out_top_left = H @ np.array(
        [0, 0, 1]
    )  # The pixel center of an (h, w) image's top left corner
    out_top_right = H @ np.array(
        [w_in - 1, 0, 1]
    )  # The pixel center of an (h, w) image's top right corner
    out_bottom_left = H @ np.array(
        [0, h_in - 1, 1]
    )  # The pixel center of an (h, w) image's bottom left corner
    out_bottom_right = H @ np.array(
        [w_in - 1, h_in - 1, 1]
    )  # The pixel center of an (h, w) image's bottom right corner

    out_top_left = normalize(out_top_left)
    out_top_right = normalize(out_top_right)
    out_bottom_left = normalize(out_bottom_left)
    out_bottom_right = normalize(out_bottom_right)

    # (x_min, y_min) represent the top-left corner of the warped image in the original image's space.
    x_min = math.floor(
        min(out_top_left[0], out_top_right[0], out_bottom_left[0], out_bottom_right[0])
    )
    x_max = math.ceil(
        max(out_top_left[0], out_top_right[0], out_bottom_left[0], out_bottom_right[0])
    )
    y_min = math.floor(
        min(out_top_left[1], out_top_right[1], out_bottom_left[1], out_bottom_right[1])
    )
    y_max = math.ceil(
        max(out_top_left[1], out_top_right[1], out_bottom_left[1], out_bottom_right[1])
    )

    h_out = y_max - y_min + 1
    w_out = x_max - x_min + 1

    # Top-left pixel in out (matrix index (0, 0)) corresponds
    # to the pixel location (x_min, y_min) in the warped image.
    # Top-left pixel in out (matrix index (0, 0)) corresponds
    # to the pixel location (x_min, y_min) in the warped image.
    if im.ndim == 3:
        out = np.zeros((h_out, w_out, c_in))
    else:
        out = np.zeros((h_out, w_out))

    # 2D mask to mark which pixels in the output had valid source mappings.
    # Used as alpha channel later to distinguish output pixel = 0 because
    # it came from a 0 pixel in the source vs. output pixel = 0 because it
    # had no valid source mapping.
    mask = np.zeros((h_out, w_out)).astype(bool)

    H_inv = np.linalg.inv(H)

    # Iterate through pixel coordinates in the output image.
    for y in range(h_out):
        for x in range(w_out):
            # For each pixel in the output, compute which source pixels it came from
            # and "gather" colors from the source pixels.

            # First transform 0-indexed (x, y) into pixel coordinates in the warped image space.
            dest_coords = np.array([x + x_min, y + y_min, 1])
            source_coords = normalize(H_inv @ dest_coords)
            if source_coords is None:
                continue  # Skip if source_coord's final component is zero or infinity
            source_x = source_coords[0]
            source_y = source_coords[1]

            neighbor_1 = [
                math.floor(source_x),
                math.floor(source_y),
            ]  # Neighbor above and to the left
            neighbor_2 = [
                math.floor(source_x),
                math.floor(source_y) + 1,
            ]  # Neighbor below and to the left
            neighbor_3 = [
                math.floor(source_x) + 1,
                math.floor(source_y) + 1,
            ]  # Neighbor below and to the right
            neighbor_4 = [
                math.floor(source_x) + 1,
                math.floor(source_y),
            ]  # Neighbor above and to the right

            # Each neighbor gets weighted by the area of the rectangle diagonal to it.
            # If a neighbor is out of bounds, set its weight to 0.
            out_value = 0
            if 0 <= neighbor_1[0] < w_in and 0 <= neighbor_1[1] < h_in:
                weight_1 = abs(source_x - neighbor_3[0]) * abs(source_y - neighbor_3[1])
                n1_x, n1_y = neighbor_1
                out_value += weight_1 * im[n1_y, n1_x]
            else:
                weight_1 = 0

            if 0 <= neighbor_2[0] < w_in and 0 <= neighbor_2[1] < h_in:
                weight_2 = abs(source_x - neighbor_4[0]) * abs(source_y - neighbor_4[1])
                n2_x, n2_y = neighbor_2
                out_value += weight_2 * im[n2_y, n2_x]
            else:
                weight_2 = 0

            if 0 <= neighbor_3[0] < w_in and 0 <= neighbor_3[1] < h_in:
                weight_3 = abs(source_x - neighbor_1[0]) * abs(source_y - neighbor_1[1])
                n3_x, n3_y = neighbor_3
                out_value += weight_3 * im[n3_y, n3_x]
            else:
                weight_3 = 0

            if 0 <= neighbor_4[0] < w_in and 0 <= neighbor_4[1] < h_in:
                weight_4 = abs(source_x - neighbor_2[0]) * abs(source_y - neighbor_2[1])
                n4_x, n4_y = neighbor_4
                out_value += weight_4 * im[n4_y, n4_x]
            else:
                weight_4 = 0

            # The pixel at (x, y) in the output is valid if we interpolate
            # from the source with at least one non-zero weight
            if weight_1 + weight_2 + weight_3 + weight_4 > 0:
                out_value /= weight_1 + weight_2 + weight_3 + weight_4
                out[y, x] = out_value
                mask[y, x] = True

    return out, mask, (x_min, y_min)


def main():
    print("Hello world!")
    # im1_pts = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    # im2_pts = np.array([[-1, -2], [-3, -4], [-5, -6], [-7, -8]])
    # computeH(im1_pts, im2_pts)

    # img1 = img_to_np(DATA_DIR / "engineering_1.jpg")
    # img2 = img_to_np(DATA_DIR / "engineering_2.jpg")

    # im1_pts, im2_pts = get_correspondences(img1, img2)

    # H = computeH(im1_pts, im2_pts)
    # print(f"Recovered homography matrix: {H}")

    warp_im1 = img_to_np(DATA_DIR / "parthenon.jpg")
    h, w, _ = warp_im1.shape
    warp_im2 = np.zeros_like(warp_im1)
    size_of_corner = max(h // 15, w // 15)
    warp_im2[
        h // 2 - size_of_corner : h // 2 + size_of_corner,
        w // 2 - size_of_corner : w // 2 + size_of_corner,
        :,
    ] = 1

    warp_im1_pts, warp_im2_pts = get_correspondences(warp_im1, warp_im2)

    warp_H = computeH(warp_im1_pts, warp_im2_pts)

    print(f"Recovered homography matrix: {warp_H}")

    nn_warp, mask, (x_min, y_min) = warpImageNearestNeighbor(warp_im1, warp_H)

    bilinear_warp, mask, (x_min, y_min) = warpImageBilinear(warp_im1, warp_H)

    fig, axs = plt.subplots(1, 2, figsize=(12, 6))
    axs[0].imshow(nn_warp)
    axs[0].set_title("Warp (nearest neighbors inverse warp)")

    axs[1].imshow(bilinear_warp)
    axs[1].set_title("Warp (bilinear interpolation inverse warp)")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
