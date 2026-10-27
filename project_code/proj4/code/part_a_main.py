import math
import numpy as np
import cv2 as cv
import scipy
import skimage as sk
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = Path("data")
OUTPUT_DIR = Path("out")


def img_to_np(input_file_path, resize=False, grayscale=False):
    """Reads an image given an input_file_path, and returns a NumPy ndarray"""
    img = sk.io.imread(input_file_path)
    img = sk.img_as_float(img)

    # Convert 4-channeled RGBA images into RGB images
    if img.shape[-1] > 3:
        img = sk.color.rgba2rgb(img)

    if grayscale:
        img = sk.color.rgb2gray(img)

    if resize:
        h, w = img.shape[:2]
        if w > 1000 or h > 1000:
            new_w = 960
            new_h = round(new_w * h / w)
            img = sk.transform.resize(img, (new_h, new_w), anti_aliasing=True)

    return img


def save_np_as_img(output_path, arr):
    """Helper function to convert a NumPy ndarray into uint8 for saving"""
    if np.issubdtype(arr.dtype, np.floating):
        arr = (arr * 255.0).astype(np.uint8)

    sk.io.imsave(output_path, arr)

    print(f"Saved image to {output_path}")


def make_2d_gaussian_kernel(size=None, sigma=None):
    """Make a 2D Gaussian kernel"""
    # Size needs to be odd and positive
    if size is not None:
        # OpenCV will automatically calculate a sigma based on the size if sigma is non-positive
        gaussian_filter = cv.getGaussianKernel(size, sigma=0)
    elif sigma is not None:
        # Rule of thumb for Gaussians: set filter half-width to about 3 sigma
        kernel_size = 2 * int(np.ceil(3 * sigma)) + 1
        gaussian_filter = cv.getGaussianKernel(kernel_size, sigma)
    else:
        gaussian_filter = cv.getGaussianKernel(ksize=3, sigma=0)

    return gaussian_filter @ gaussian_filter.T


def get_correspondences(
    im1: np.ndarray,
    im2: np.ndarray,
    num_correspondences=8,
    im1_title=None,
    im2_title=None,
    output_base_name=None,
) -> tuple:
    """
    Interactive window that shows the 2 images side-by-side.
    Users can alternate clicking points in image 1 and image 2.
    """
    colors = list(mcolors.BASE_COLORS.keys())

    fig, axs = plt.subplots(1, 2, figsize=(16, 6))
    axs[0].imshow(im1)
    axs[0].set_title(im1_title if im1_title else "Image 1")
    axs[0].gid = "image_1"  # Tag each subplot with a label

    axs[1].imshow(im2)
    axs[1].set_title(im2_title if im2_title else "Image 2")
    axs[1].gid = "image_2"  # Tag each subplot with a label

    fig.suptitle(
        f"Correspondences between {im1_title if im1_title else 'Image 1'} and {im2_title if im2_title else 'Image 1'}\nClick {num_correspondences} points in each image (press esc to undo)"
    )

    im1_pts = []
    im1_markers = []  # List of marker objects returned by .plot
    im2_pts = []
    im2_markers = []
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
            im1_markers.append(
                axs[0].plot(
                    event.xdata,
                    event.ydata,
                    color=colors[len(im1_pts) % len(colors)],
                    marker="o",
                    markersize=6,
                )[0]
            )
            fig.canvas.draw_idle()
            im1_pts.append([event.xdata, event.ydata])
            next_axs = (next_axs + 1) % 2
        elif event.inaxes.gid == "image_2" and next_axs == 1:
            print(
                f"Captured click at ({event.xdata:.2f}, {event.ydata:.2f}) in image 2"
            )
            im2_markers.append(
                axs[1].plot(
                    event.xdata,
                    event.ydata,
                    color=colors[len(im2_pts) % len(colors)],
                    marker="o",
                    markersize=6,
                )[0]
            )
            fig.canvas.draw_idle()
            im2_pts.append([event.xdata, event.ydata])
            next_axs = (next_axs + 1) % 2
        else:
            print(f"Please select a point in image {next_axs + 1} next")

        if len(im1_pts) == num_correspondences and len(im2_pts) == num_correspondences:
            # Close the figure once user has selected num_correspondences points in both images
            plt.savefig(
                f"{OUTPUT_DIR}/{output_base_name + '_correspondences' if output_base_name else 'correspondences'}.jpg",
                bbox_inches="tight",
            )
            plt.close(fig)

    def on_keypress(event):
        """
        Undo the last selected point if the user enters "escape"
        """
        print("Keypress:", event.key)
        if event.key != "escape":
            return
        if len(im1_pts) == 0 and len(im2_pts) == 0:
            return

        nonlocal next_axs
        last_axs = (next_axs - 1) % 2
        if last_axs == 0:
            im1_pts.pop()
            last_marker = im1_markers.pop()
        else:
            im2_pts.pop()
            last_marker = im2_markers.pop()

        last_marker.remove()  # Remove marker from the plot
        next_axs = last_axs
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("key_press_event", on_keypress)
    plt.tight_layout()

    plt.show()
    print(f"Collected {len(im1_pts)} correspondences")
    return np.array(im1_pts), np.array(im2_pts)


def computeH(im1_pts: np.ndarray, im2_pts: np.ndarray, verbose: bool = False):
    """
    Compute the homography matrix that transforms image 1 onto image 2, given correspondence point pairs.

    Args:
        im1_pts, im2_pts: (N, 2) matrices of N point correspondences between the two images
            - Each row is an (x, y) coordinate pair
            - To recover the matrix H, the inputs must contain at least 4 correspondences
        verbose: whether or not to print out the system of equations and recovered H.

    Returns:
        H: the recovered (3x3) homography matrix
    """
    # Ah = b where h is a vector holding the 8 unknown entries of H
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

    if verbose:
        print(
            f"Ah = b\n\nA:\n{np.array2string(A, precision=2)}\n\nb:\n{np.array2string(b, precision=2)}"
        )
    h, _, _, _ = np.linalg.lstsq(A, b)
    if verbose:
        print(f"h found via least-squares:\n{np.array2string(h, precision=2)}")

    # Convert h from a column vector into a matrix
    H = np.ones((3, 3))
    for i in range(8):
        row, col = i // 3, i % 3
        H[row, col] = h[i]
    if verbose:
        print(f"Recovered homography matrix H:\n{np.array2string(H, precision=2)}")
    return H


def normalize(homogeneous_coord: np.ndarray):
    """Normalizes 3D homogeneous coordinates s.t. its last component = 1"""
    if homogeneous_coord.ndim == 1:
        denominator = homogeneous_coord[-1]
    elif (
        homogeneous_coord.ndim == 2
    ):  # Batched homogenous coordinates have shape (3, N)
        denominator = homogeneous_coord[-1:,]
    else:
        print(
            f"Invalid shape when normalizing homogenous coordinates: {homogeneous_coord.shape}"
        )
        return None  # Invalid shape

    valid = (denominator != 0) & np.isfinite(denominator)
    normalized = np.divide(
        homogeneous_coord,
        denominator,
        out=np.zeros_like(homogeneous_coord),
        where=valid,
    )
    return normalized, valid


def warpImageNearestNeighbor(im, H):
    """
    Warp im by applying the homography H.
    Compute the pixel values in the warped image using inverse warping (nearest neighbors interpolation).
    """
    print("===== Warping image using nearest neighbor inverse warping =====")
    if im.ndim == 2:
        im = np.expand_dims(im, axis=2)  # Add singleton dimension to grayscale images

    h_in, w_in, c_in = im.shape

    x_min, x_max, y_min, y_max = get_warped_corners(im, H)

    # Top-left pixel in out (matrix index (0, 0)) corresponds
    # to the pixel location (x_min, y_min) in the warped image.
    h_out = y_max - y_min + 1
    w_out = x_max - x_min + 1

    out = np.zeros((h_out, w_out, c_in))

    # 2D mask to mark which pixels in the output had valid source mappings.
    # Used as alpha channel later to distinguish output pixel = 0 because
    # it came from a 0 pixel in the source vs. output pixel = 0 because it
    # had no valid source mapping.
    mask = np.zeros((h_out, w_out, 1)).astype(bool)

    H_inv = np.linalg.inv(H)

    # Iterate through pixel coordinate in the output image.
    for y in range(h_out):
        # First transform 0-indexed (x, y) into pixel coordinates in the warped image space.
        # Also add a 3rd component of all 1's to transform into homogeneous
        # coordinates for homography matmul.
        dest_row = np.stack(
            [
                np.arange(
                    x_min, x_max + 1, 1
                ),  # x-coordinates for this row go from x_min to x_max
                np.full((w_out), y + y_min),  # y-coordinates for this row: y + y_min
                np.ones(
                    w_out
                ),  # homogeneous coordinates have a 1 in the last component
            ],
            axis=0,
        )
        source_coords, valid = normalize(H_inv @ dest_row)
        source_coords = source_coords.T  # (3, N) --> (N, 3)
        valid = np.squeeze(
            valid.T
        )  # (1, N) --> (N,) for combining with boolean operators later
        source_x = np.round(source_coords[:, 0]).astype(int)
        source_y = np.round(source_coords[:, 1]).astype(int)

        valid = (
            (0 <= source_x)
            & (source_x < w_in)
            & (0 <= source_y)
            & (source_y < h_in)
            & valid
        )

        # Clip to prevent out-of-bounds errors in case the transformation
        # maps to pixel positions in the source image that are out-of-bounds.
        safe_source_x = np.clip(source_x, 0, w_in - 1)
        safe_source_y = np.clip(source_y, 0, h_in - 1)

        # Matrix coordinates (x, y) correspond to pixel positions row=y, col=x
        out[y, valid, :] = im[safe_source_y[valid], safe_source_x[valid]]
        mask[y, valid, 0] = True

    return out, mask, (x_min, x_max, y_min, y_max)


def warpImageBilinear(im, H):
    """
    Warp im by applying the homography H.
    Compute the pixel values in the warped image using inverse warping (bilinear interpolation).
    """
    print("===== Warping image using bilinear interpolation inverse warping =====")

    if im.ndim == 2:
        im = np.expand_dims(im, axis=2)  # Add singleton dimension to grayscale images

    h_in, w_in, c_in = im.shape

    x_min, x_max, y_min, y_max = get_warped_corners(im, H)

    # Top-left pixel in out (matrix index (0, 0)) corresponds
    # to the pixel location (x_min, y_min) in the warped image.
    h_out = y_max - y_min + 1
    w_out = x_max - x_min + 1

    out = np.zeros((h_out, w_out, c_in))

    # 2D mask to mark which pixels in the output had valid source mappings.
    # Used as alpha channel later to distinguish output pixel = 0 because
    # it came from a 0 pixel in the source vs. output pixel = 0 because it
    # had no valid source mapping.
    mask = np.zeros((h_out, w_out, 1)).astype(bool)

    H_inv = np.linalg.inv(H)

    # Iterate through pixel coordinates in the output image.
    for y in range(h_out):
        # For each pixel in the output, compute which source pixels it came from
        # and "gather" colors from the source pixels.
        dest_row = np.stack(
            [
                np.arange(
                    x_min, x_max + 1, 1
                ),  # x-coordinates for this row go from x_min to x_max
                np.full((w_out), y + y_min),  # y-coordinates for this row: y + y_min
                np.ones(
                    w_out
                ),  # homogeneous coordinates have a 1 in the last component
            ],
            axis=0,
        )

        source_coords, valid = normalize(H_inv @ dest_row)
        source_coords = source_coords.T  # (3, N) --> (N, 3)
        valid = np.squeeze(
            valid.T
        )  # (1, N) --> (N,) for combining with boolean operators later
        source_x = source_coords[:, 0]
        source_y = source_coords[:, 1]

        left_x = np.floor(source_x).astype(int)
        right_x = left_x + 1
        top_y = np.floor(source_y).astype(int)
        bottom_y = top_y + 1

        # Neighbor above and to the left has x,y coordinates (left_x, top_y) which correspond to pixel positions at row top_y and col left_x
        n1_valid = (
            (0 <= left_x) & (left_x < w_in) & (0 <= top_y) & (top_y < h_in) & valid
        )

        # Neighbor below and to the left, with x,y coordinates (left_x, bottom_y) and pixel positions row=bottom_y, col=left_x
        n2_valid = (
            (0 <= left_x)
            & (left_x < w_in)
            & (0 <= bottom_y)
            & (bottom_y < h_in)
            & valid
        )

        # Neighbor below and to the right, with x,y coordinates (right_x, bottom_y) and pixel positions row=bottom_y, col=right_x
        n3_valid = (
            (0 <= right_x)
            & (right_x < w_in)
            & (0 <= bottom_y)
            & (bottom_y < h_in)
            & valid
        )

        # Neighbor above and to the right, with x,y coordinates (right_x, top_y) and pixel positions row=top_y, col=right_x
        n4_valid = (
            (0 <= right_x) & (right_x < w_in) & (0 <= top_y) & (top_y < h_in) & valid
        )

        # Each neighbor gets weighted by the area of the rectangle diagonal to it.
        # If a neighbor is out of bounds, set its weight to 0.
        weight_1 = abs(source_x - right_x) * abs(
            source_y - bottom_y
        )  # weight of neighbor 1 uses neighbor 3's coords to calculate area
        weight_1 = np.expand_dims(weight_1, axis=1)  # (H, W) --> (H, W, 1)
        weight_1[~n1_valid] = (
            0  # if neighbor 1's coordinates are out-of-bounds, zero out its weight
        )

        weight_2 = abs(source_x - right_x) * abs(source_y - top_y)
        weight_2 = np.expand_dims(weight_2, axis=1)  # (H, W) --> (H, W, 1)
        weight_2[~n2_valid] = 0

        weight_3 = abs(source_x - left_x) * abs(source_y - top_y)
        weight_3 = np.expand_dims(weight_3, axis=1)  # (H, W) --> (H, W, 1)
        weight_3[~n3_valid] = 0

        weight_4 = abs(source_x - left_x) * abs(source_y - bottom_y)
        weight_4 = np.expand_dims(weight_4, axis=1)  # (H, W) --> (H, W, 1)
        weight_4[~n4_valid] = 0

        # Clip to prevent out-of-bounds errors in case the transformation
        # maps to pixel positions in the source image that are out-of-bounds.
        safe_left_x = np.clip(left_x, 0, w_in - 1)
        safe_right_x = np.clip(right_x, 0, w_in - 1)
        safe_bottom_y = np.clip(bottom_y, 0, h_in - 1)
        safe_top_y = np.clip(top_y, 0, h_in - 1)

        # The pixel at (x, y) in the output is valid if we interpolate
        # from the source with at least one non-zero weight
        weights = weight_1 + weight_2 + weight_3 + weight_4
        out_value = np.divide(
            weight_1 * im[safe_top_y, safe_left_x]
            + weight_2 * im[safe_bottom_y, safe_left_x]
            + weight_3 * im[safe_bottom_y, safe_right_x]
            + weight_4 * im[safe_top_y, safe_right_x],
            weights,
            out=np.zeros_like(out[y, :]),
            where=(weights > 0),
        )
        out[y, :] = out_value
        mask[y, :] = (weights > 0).astype(bool)

    return out, mask, (x_min, x_max, y_min, y_max)


def rectify(
    im: np.ndarray,
    reference_rectangle: np.ndarray | None = None,
    output_base_name: str | None = None,
):
    """
    Rectifies an image by transforming it such that a skewed rectangle in the image
    matches up with a reference rectangle with right angles and parallel sides.

    Uses the get_correspondences, computeH, and interpolation functions as helpers.
    Plots, saves, and displays a plot of the original image and the reference rectangle
    with annotated correspondences. Also displays the rectification results.

    Args:
        im: an image as an np.ndarray
        reference_rectangle: optional np.ndarray of a rectangle to use as the image
            to transform im to align with. If None, this function creates a reference
            rectangle with the same shape as im and a square at the center.
        output_base_name: the base name of the output path to save plots to.
    """
    h, w, _ = im.shape
    if reference_rectangle is None:
        reference_rectangle = np.zeros_like(im)
        size_of_rectangle = max(h // 15, w // 15)
        reference_rectangle[
            h // 2 - size_of_rectangle : h // 2 + size_of_rectangle,
            w // 2 - size_of_rectangle : w // 2 + size_of_rectangle,
            :,
        ] = 1

    warp_im1_pts, warp_im2_pts = get_correspondences(
        im,
        reference_rectangle,
        num_correspondences=4,
        output_base_name=output_base_name,
    )
    warp_H = computeH(warp_im1_pts, warp_im2_pts)

    nn_warp, _, _ = warpImageNearestNeighbor(im, warp_H)

    bilinear_warp, _, _ = warpImageBilinear(im, warp_H)

    scatter_colors = list(mcolors.BASE_COLORS.keys())[: len(warp_im1_pts)]
    fig, axs = plt.subplots(2, 2, figsize=(8, 8))
    axs[0, 0].imshow(im)
    axs[0, 0].set_title("Original image")
    axs[0, 0].scatter(warp_im1_pts[:, 0], warp_im1_pts[:, 1], s=6, c=scatter_colors)

    axs[0, 1].imshow(reference_rectangle)
    axs[0, 1].set_title("Reference rectangle")
    axs[0, 1].scatter(warp_im2_pts[:, 0], warp_im2_pts[:, 1], s=6, c=scatter_colors)

    axs[1, 0].imshow(nn_warp)
    axs[1, 0].set_title("Warp (nearest neighbors inverse warp)")

    axs[1, 1].imshow(bilinear_warp)
    axs[1, 1].set_title("Warp (bilinear interpolation inverse warp)")

    fig.suptitle(
        f"Rectification{': ' + output_base_name if output_base_name else None}"
    )
    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/{output_base_name + '_rectify' if output_base_name else 'rectify'}.jpg",
        bbox_inches="tight",
    )
    plt.show()

    save_np_as_img(
        f"{OUTPUT_DIR}/{output_base_name + '_nearest_neighbors_rectify' if output_base_name else 'nearest_neighbors_rectify'}.jpg",
        nn_warp,
    )

    save_np_as_img(
        f"{OUTPUT_DIR}/{output_base_name + '_bilinear_rectify' if output_base_name else 'bilinear_rectify'}.jpg",
        bilinear_warp,
    )


def get_warped_corners(im: np.ndarray, H: np.ndarray):
    """
    Compute where the corners of im would get mapped to after im gets transformed by H.

    Args:
        im: an image
        H: a homography matrix that transforms im into a warped space.

    Returns:
        x_min, x_max, y_min, y_max: the coordinates corresponding to im's corners after warping,
            written in terms of the image's original space.
    """
    h_in, w_in, _ = im.shape
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

    out_top_left, _ = normalize(out_top_left)
    out_top_right, _ = normalize(out_top_right)
    out_bottom_left, _ = normalize(out_bottom_left)
    out_bottom_right, _ = normalize(out_bottom_right)

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

    return x_min, x_max, y_min, y_max


def gaussian_stack(
    im=None,
    max_levels=2,
):
    """
    Build a Gaussian stack of im.
    """
    print("===== Building Gaussian stack =====")
    h, w = im.shape[:2]
    if im.ndim == 3:
        r, g, b = im[:, :, 0], im[:, :, 1], im[:, :, 2]

    # Rule of thumb for Gaussians: set filter half-width to about 3 sigma
    # Set max kernel size to ~ 1/2 width
    max_kernel_size = min(h, w) // 2
    max_sigma = (max_kernel_size) // 6

    sigma = 1
    stack = [im]

    # Implement Gaussian stack by applying bigger blurs (bigger sigma + kernel size)
    while sigma <= max_sigma and len(stack) < max_levels:
        gaussian_kernel = make_2d_gaussian_kernel(sigma=sigma)
        if im.ndim == 3:
            conv_r = scipy.signal.convolve2d(
                r, gaussian_kernel, mode="same", fillvalue=0
            )
            conv_g = scipy.signal.convolve2d(
                g, gaussian_kernel, mode="same", fillvalue=0
            )
            conv_b = scipy.signal.convolve2d(
                b, gaussian_kernel, mode="same", fillvalue=0
            )

            conv_stacked = np.dstack([conv_r, conv_g, conv_b])
            stack.append(conv_stacked)
        else:
            conv = scipy.signal.convolve2d(
                im, gaussian_kernel, mode="same", fillvalue=0
            )
            stack.append(conv)
        sigma *= 2

    return np.array(stack)


def laplacian_stack(im, max_levels=2):
    """
    Build a Laplacian stack of im.
    """
    print("===== Building Laplacian stack =====")
    # level 0 = highest freq, level[-1] = lowest freq (most blurred)
    gaussian_levels = gaussian_stack(im, max_levels=max_levels)
    stack = []

    # Compute Laplacian levels by subtracting adjacent Gaussian levels
    # L_i = G_i - G_{i + 1}
    # L_i represents the info lost when going from G_i to G_{i + 1}
    for i in range(len(gaussian_levels) - 1):
        G_i = gaussian_levels[i]
        G_iplus1 = gaussian_levels[i + 1]
        L_i = G_i - G_iplus1
        stack.append(L_i)

    # Final level of Laplacian stack should be the coarsest (blurriest) Gaussian level
    stack.append(gaussian_levels[-1])

    return np.array(stack)


def make_mosaic(images, output_base_name, num_correspondences=8):
    """
    Create a mosaic by stitching together multiple images.

    1. Find correspondences between neighboring pairs of input images,
        and compute homographies that map an image to the next image in the list: H_(1->2), H_(2->3), ...
    2. Compose a transfrom from each image into the center image, and store a final image-to-center homography for each image:
        - To map image 1 into image 3: p' = H_(2->3) H_(1->2) p
        - H_(3->3) is just the identity matrix.
        - To map image 5 into image 3: H_(5->3) = (H_(4->5) H_(3->4))^-1 = H^-1_(3->4) H^-1_(4->5) = H_(4->3) H_(5->4)
            - The transformation from image 3's coordinates to image 5's coordinates: p' = H_(4->5) H_(3->4) p
    3. Compute the bounding box of the shared canvas from all the transforms:
        a. For each image, transform its 4 corners using the image-to-center homography and normalize
            the homogeneous coordinates after warping.
        b. Find the minimum and maximum x and y across all images, then take the floor/ceil of the minimas/maximas
            to compute the dimensions of the shared projective plane.
    4. Warp each image and mask onto their own copies of the projective plane canvas.
    5. Blend all the image canvases together using Laplacian stacks and Gaussian stacks of their masks as weights.

    Args:
        images: list of np.ndarrays. The images should be ordered such that consecutive images overlap
            because this algorithm computes homographies between adjacent pairs of images.
        output_base_name: the base name of the output path to save plots to.
        num_correspondences: the number of corresponding point pairs to
            pick between 2 images; needs to be >= 4 to compute homography matrix H.
    Returns:
        mosaic: np.ndarray of the final mosaic

    Also creates a plot of the input images alongside the final mosaic, and saves both
    the plot and the final mosaic to OUTPUT_DIR.
    """
    num_images = len(images)

    # Use the middle image in the input list as the image at the center
    # of the shared projective plane.
    center_im_idx = num_images // 2
    center_im = images[center_im_idx]
    h_center, w_center = center_im.shape[:2]

    homographies = []  # homographies[i] is the transform that maps im_{i} to im_{i+1}
    for i in range(num_images - 1):
        im1, im2 = images[i], images[i + 1]
        im1_pts, im2_pts = get_correspondences(
            im1,
            im2,
            num_correspondences=num_correspondences,
            im1_title=f"Image {i}",
            im2_title=f"Image {i + 1}",
            output_base_name=f"{output_base_name}_{i}_{i + 1}",
        )
        H_im1_to_im2 = computeH(im1_pts, im2_pts)
        homographies.append(H_im1_to_im2)

    homography_to_center = {}
    curr_H = np.eye(3)
    homography_to_center[center_im_idx] = curr_H
    # Compute homographies that map images on the left of center_im to the center_im
    # by composing homographies: H_(1->3) = H_(2->3) H_(1->2)
    for i in range(center_im_idx - 1, -1, -1):
        H_prev_to_i = homographies[i]
        curr_H = curr_H @ H_prev_to_i
        homography_to_center[i] = curr_H

    curr_H = np.eye(3)
    # Compute homographies that map images on the right of center_im to the center_im
    # by composing inverse homographies: H_(5->3) = H^-1_(3->4) H^-1_(4->5)
    for i in range(center_im_idx + 1, num_images):
        H_prev_to_i = homographies[i - 1]  #
        H_inv = np.linalg.inv(H_prev_to_i)
        curr_H = curr_H @ H_inv
        homography_to_center[i] = curr_H

    idx_to_warped = {}
    x_mins = []
    x_maxes = []
    y_mins = []
    y_maxes = []
    for idx, im in enumerate(images):
        H_to_center = homography_to_center[idx]
        out, mask, corners = warpImageBilinear(im, H_to_center)
        x_min, x_max, y_min, y_max = corners

        idx_to_warped[idx] = {"out": out, "mask": mask, "corners": corners}
        x_mins.append(x_min)
        x_maxes.append(x_max)
        y_mins.append(y_min)
        y_maxes.append(y_max)

    # Compute dimensions of shared canvas
    x_min_canvas = math.floor(min(x_mins + [0]))
    x_max_canvas = math.ceil(
        max(x_maxes + [w_center - 1])
    )  # Largest x-coordinate of any pixel in center is w_center - 1
    y_min_canvas = math.floor(min(y_mins + [0]))
    y_max_canvas = math.ceil(max(y_maxes + [h_center - 1]))

    canvas_w = x_max_canvas - x_min_canvas + 1
    canvas_h = y_max_canvas - y_min_canvas + 1

    # Center image's top-left pixel (0, 0) should be placed at row -y_min, col -x_min in the canvas
    canvas = np.zeros((canvas_h, canvas_w, 3))
    # Binary mask that is an additive sum of all the warped image's masks.
    # Used as a final mask to crop out any blurry halos in the final canvas around the final mosaic
    # that result from the gaussian weights blurring outer pixels into neighboring pixels on the canvas.
    final_binary_mask = np.zeros((canvas_h, canvas_w, 3))

    # Place each image or mask in its position on a separate canvas (all canvases have the same dimension
    # as the final, shared canvas).
    stack_depth = 2
    laplacian_stacks = []
    gaussian_mask_stacks = []
    for idx, im in enumerate(images):
        curr_canvas = canvas.copy()
        curr_canvas_mask = canvas.copy()

        out = idx_to_warped[idx]["out"]
        mask = idx_to_warped[idx]["mask"]
        x_min, x_max, y_min, y_max = idx_to_warped[idx]["corners"]
        # Each image's top-left pixels should get translated to y_min - y_min_canvas, x_min - x_min_canvas
        # in the final shared canvas after being warped.
        # Center image's top-left pixel (0, 0) should be placed at row -y_min_canvas, col -x_min_canvas in the canvas.
        curr_canvas[
            y_min - y_min_canvas : y_max - y_min_canvas + 1,
            x_min - x_min_canvas : x_max - x_min_canvas + 1,
        ] = out

        curr_canvas_mask[
            y_min - y_min_canvas : y_max - y_min_canvas + 1,
            x_min - x_min_canvas : x_max - x_min_canvas + 1,
        ] = mask.astype(float)

        final_binary_mask += curr_canvas_mask
        lap = laplacian_stack(curr_canvas, stack_depth)  # (depth, H, W, 3)
        gauss = gaussian_stack(curr_canvas_mask, stack_depth)

        laplacian_stacks.append(lap)
        gaussian_mask_stacks.append(gauss)

    laplacian_stacks = np.stack(
        laplacian_stacks, axis=1
    )  # list with num_images items, each of shape (depth, H, W, 3) --> (depth, num_images, H, W, 3)
    gaussian_mask_stacks = np.stack(
        gaussian_mask_stacks, axis=1
    )  # list with num_images items, each of shape (depth, H, W, 3) --> (depth, num_images, H, W, 3)

    mosaic = np.zeros_like(canvas)
    for laplacians, gaussians in zip(laplacian_stacks, gaussian_mask_stacks):
        blend = np.zeros_like(canvas)
        gaussian_weights = np.zeros_like(canvas)
        for i in range(num_images):
            blend += gaussians[i] * laplacians[i]
            gaussian_weights += gaussians[i]

        blend = np.divide(
            blend,
            gaussian_weights,
            out=np.zeros_like(blend),
            where=gaussian_weights > 0,
        )

        mosaic += blend

    # final_binary_mask should be 1 if at least one validity mask covered this pixel,
    # AKA at least 1 warped image mapped to this pixel in the shared projective view.
    mosaic = mosaic * (final_binary_mask > 0)
    mosaic = np.clip(mosaic, 0, 1.0)

    num_rows = math.ceil(num_images / 3.0) + 1
    num_cols = 3
    fig, axs = plt.subplots(
        num_rows,
        num_cols,
        figsize=(4 * num_cols, 3 * num_rows),
    )

    for idx, ax in enumerate(axs.flatten()):
        if idx >= len(images):
            ax.set_visible(False)
        else:
            ax.imshow(images[idx])
            ax.set_title(
                f"Image {idx + 1}{' (center)' if idx == center_im_idx else ''}"
            )

    axs[-1, num_cols // 2].set_visible(True)
    axs[-1, num_cols // 2].imshow(mosaic)

    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/{output_base_name}_mosaic_plots.jpg",
        bbox_inches="tight",
    )
    plt.show()

    plt.imshow(mosaic)
    plt.show()

    mosaic_saved = (mosaic * 255.0).astype(np.uint8)
    sk.io.imsave(f"{OUTPUT_DIR}/{output_base_name}_mosaic.jpg", mosaic_saved)
    print(f"Saved image to {OUTPUT_DIR}/{output_base_name}_mosaic.jpg")

    return mosaic


def main():
    print("===== (Auto)stitching and Photo Mosaics =====")
    # Section A.2: Recover Homographies
    gec_1 = img_to_np(DATA_DIR / "gec_1.jpg")
    gec_2 = img_to_np(DATA_DIR / "gec_2.jpg")
    gec_3 = img_to_np(DATA_DIR / "gec_3.jpg")

    gec_1_pts, gec_2_pts = get_correspondences(
        gec_1, gec_2, num_correspondences=8, output_base_name="gec_1_2"
    )
    H = computeH(gec_1_pts, gec_2_pts, verbose=True)

    # Section A.3: Warp the Images (rectification)
    painting_im = img_to_np(DATA_DIR / "painting.jpg")
    rectify(painting_im, output_base_name="painting")

    pompeii_im = img_to_np(DATA_DIR / "pompeii.jpg")
    rectify(pompeii_im, output_base_name="pompeii")

    wall_fresco_im = img_to_np(DATA_DIR / "wall_fresco.jpg")
    rectify(wall_fresco_im, output_base_name="wall_fresco")

    # Section A.4: Blend the Images into a Mosaic
    gec_1 = img_to_np(DATA_DIR / "gec_1.jpg")
    gec_2 = img_to_np(DATA_DIR / "gec_2.jpg")
    gec_3 = img_to_np(DATA_DIR / "gec_3.jpg")

    make_mosaic(
        [gec_1, gec_2, gec_3],
        "gec",
        6,
    )

    campus_1 = img_to_np(DATA_DIR / "campus_1.jpg")
    campus_2 = img_to_np(DATA_DIR / "campus_2.jpg")
    campus_3 = img_to_np(DATA_DIR / "campus_3.jpg")
    campus_4 = img_to_np(DATA_DIR / "campus_4.jpg")
    campus_5 = img_to_np(DATA_DIR / "campus_5.jpg")

    make_mosaic(
        [campus_1, campus_2, campus_3, campus_4, campus_5],
        "campus",
        6,
    )

    kresge_1 = img_to_np(DATA_DIR / "kresge_1.jpg")
    kresge_2 = img_to_np(DATA_DIR / "kresge_2.jpg")
    kresge_3 = img_to_np(DATA_DIR / "kresge_3.jpg")
    kresge_4 = img_to_np(DATA_DIR / "kresge_4.jpg")
    kresge_5 = img_to_np(DATA_DIR / "kresge_5.jpg")

    make_mosaic(
        [kresge_1, kresge_2, kresge_3, kresge_4, kresge_5],
        "kresge",
        6,
    )


if __name__ == "__main__":
    main()
