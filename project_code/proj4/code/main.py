import math
import numpy as np
import cv2 as cv
import scipy
import skimage as sk
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from pathlib import Path

from harris import dist2, get_harris_corners

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
        im1_pts, im2_pts: (P, 2) matrices of P point correspondences between the two images
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
    num_correspondences = im1_pts.shape[0]
    A = np.zeros((2 * num_correspondences, 8))
    b = np.zeros((2 * num_correspondences,))

    for i in range(num_correspondences):
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
    """
    Normalizes 3D homogeneous coordinates s.t. its last component = 1.

    Returns a tuple of np.ndarrays: (normalized, valid)
    """
    if homogeneous_coord.ndim == 1:
        denominator = homogeneous_coord[-1]
    elif (
        homogeneous_coord.ndim == 2
    ):  # Batched homogenous coordinates have shape (3, P)
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


def harris_corner_detection(
    image: np.ndarray,
    output_base_name: str | None = None,
):
    """
    Implements section 2 of the paper: Interest Point Detection.

    Args:
        image: np.ndarray of an image.
        output_base_name: the base name of the output path to save plots to.
    Returns:
        corner_strengths: (N,) array whose ith value corresponds to the corner
            strength of interest point i.
        interest_points: (N, 2) array of xs, ys
    """
    print("===== Harris corner detection =====")

    if len(image.shape) == 3 and image.shape[2] == 3:
        bw = sk.color.rgb2gray(image)

    # h is a (height, width) array of the corner strength function of the interest points (2 * det(A) / (trace(A) + eps))
    # coords have shape (2, num_candidates)
    h, coords = get_harris_corners(bw, edge_discard=20)
    ys, xs = coords

    corner_strengths = h[ys, xs]  # (num_corners, )
    interest_points = np.stack([xs, ys], axis=1)  # (num_corners, 2)

    fig, ax = plt.subplots()
    ax.imshow(image)
    ax.set_title(f"Multi-scale Harris corners of {output_base_name}")
    ax.scatter(interest_points[:, 0], interest_points[:, 1], s=0.35)
    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/{output_base_name + '_harris_corners' if output_base_name else 'harris_corners'}.jpg",
        bbox_inches="tight",
    )
    plt.show()
    return corner_strengths, interest_points


def adaptive_nonmaximal_suppression(
    image: np.ndarray,
    corner_strengths: np.ndarray,
    interest_points: np.ndarray,
    n_ip: int = 500,
    c_robust: float = 0.9,
    output_base_name: str | None = None,
    plot_comparison: bool = False,
    verbose: bool = False,
):
    """
    Implements section 3 of the paper: Adaptive Non-Maximal Suppression.

    Uses adaptive non-maximal suppression to select a fixed number of interest points
    that are well-distributed throughout the image.

    Adaptive non-maximal suppression:
    1. For each interest point, calculate its suppression radius: r_i = min_j |p_i - p_j| s.t. corner_strength(i) < c_robust * corner_strength(j)
        a. Conceptually r_i measures how much further we must search around p_i before we find a
            meaningfully stronger corner. To calculate r_i:
            i. For each interest point p_i, find all other points p_j with a stronger corner strength.
            ii. Then, take the distance from p_i to its nearest stronger neighbor.
            iii. If no other points are stronger than p_i, assign r_i = inf.
    2. Keep n_ip with the highest suppression radius.

    Args:
        image: np.ndarray of an image.
        corner_strengths: (N,) array whose ith value corresponds to the corner
            strength of interest point i.
        interest_points: (N, 2) array of xs, ys
        n_ip: the number of interest points to keep.
        output_base_name: the base name of the output path to save plots to.
        plot_comparison: whether to plot the full set of interest points with the ANMS subset
            side-by-side, or to only plot the ANMS interest points.
        verbose: whether or not to print informational progress.

    Returns:
        kept_corner_strengths: (n_ip,) array containing the corner strengths of the kept interest points.
        kept_interest_points: (n_ip, 2) array of the interest points with the highest suppression radius.
    """
    num_candidates = interest_points.shape[0]  # Number of interest point candidates
    if n_ip > num_candidates:
        print(
            f"[ANMS] Warning: requested {n_ip} to keep, but adaptive_nonmaximal_supression only received {num_candidates} input interest points."
        )

    suppression_radius = np.full(num_candidates, fill_value=0.0)

    print("===== Adaptive non-maximal suppression =====")
    if verbose:
        print("[ANMS] Starting ANMS algorithm...")
    for i, (cs_i, p_i) in enumerate(zip(corner_strengths, interest_points)):
        stronger_points = interest_points[
            cs_i < c_robust * corner_strengths
        ]  # (num_stronger, 2)

        if len(stronger_points) == 0:
            suppression_radius[i] = np.inf
        else:
            # Need to expand p_i into (2, 1) and then transpose it into (1, 2) for dist2
            distances = np.sqrt(dist2(np.expand_dims(p_i, axis=1).T, stronger_points))
            suppression_radius[i] = np.min(distances)

    if verbose:
        print("[ANMS] ANMS algorithm completed!")

    # Sort indices such that indexing with them would sort the interest points from highest
    # suppression radius to lowest suppression radius.
    sorted_suppression_radius_idx = suppression_radius.argsort(descending=True)
    sorted_interest_points = interest_points[sorted_suppression_radius_idx]

    kept_interest_points = sorted_interest_points[:n_ip]  # (n_ip, 2)

    # Corner strengths, in the same order as kept_interest_points (highest r_i to lowest r_i)
    kept_corner_strengths = corner_strengths[sorted_suppression_radius_idx][:n_ip]

    if plot_comparison:
        fig, axs = plt.subplots(1, 2, figsize=(16, 6))
        axs[0].imshow(image)
        axs[0].set_title("Detected corners without ANMS")
        axs[0].scatter(interest_points[:, 0], interest_points[:, 1], s=0.35)
        # axs[0].scatter(random_interest_points[:, 0], random_interest_points[:, 1], s=0.35)

        axs[1].imshow(image)
        axs[1].set_title(f"{n_ip} detected corners with ANMS")
        axs[1].scatter(kept_interest_points[:, 0], kept_interest_points[:, 1], s=0.35)

        fig.suptitle(f"Multi-scale Harris corners of {output_base_name}")

        plt.tight_layout()
        plt.savefig(
            f"{OUTPUT_DIR}/{output_base_name + '_anms_comparison' if output_base_name else 'anms_comparison'}.jpg",
            bbox_inches="tight",
        )
        plt.show()
    else:
        fig, ax = plt.subplots()
        ax.imshow(image)
        ax.set_title(f"{n_ip} detected corners with ANMS")
        ax.scatter(kept_interest_points[:, 0], kept_interest_points[:, 1], s=0.35)

        plt.tight_layout()
        plt.savefig(
            f"{OUTPUT_DIR}/{output_base_name + '_anms' if output_base_name else 'anms'}.jpg",
            bbox_inches="tight",
        )
        plt.show()

    return kept_corner_strengths, kept_interest_points


def calculate_gradient(bw_image):
    H, W = bw_image.shape[:2]
    Dy = np.array([[1], [0], [-1]])
    Dx = np.array([[1, 0, -1]])
    gaussian_kernel = make_2d_gaussian_kernel(sigma=4.5)
    smoothed = scipy.signal.convolve2d(bw_image, gaussian_kernel, mode="same")

    # partial_x[row=y, col=x] = horizonal derivative at pixel at position (x, y)
    partial_x = scipy.signal.convolve2d(smoothed, Dx, mode="same")
    partial_y = scipy.signal.convolve2d(smoothed, Dy, mode="same")
    # gradient[row=y, col=x] = gradient (dx, dy) for pixel at position (x, y)
    gradient = np.stack([partial_x, partial_y], axis=2)  # (H, W, 2)
    norm = np.linalg.norm(gradient, axis=2, keepdims=True)  # (H, W, 1)
    print(f"gradient {gradient.shape}, norm {norm.shape}")
    # Normalize each position's 2D gradient vector independently.
    # u represents the unit gradient at each position (x, y).
    u = np.divide(
        gradient, norm, out=np.zeros_like(gradient), where=norm > 0
    )  # (H, W, 2)
    print(f"u {u.shape}")
    theta = np.arctan(u[:, :, 1] / u[:, :, 0])
    print(f"theta {theta.shape}")


def extract_feature_descriptors(
    image: np.ndarray,
    interest_points: np.ndarray,
    output_base_name: str,
    eps: float = 1e-8,
    num_display: int = 8,
):
    """
    Implements section 4 of the paper: Feature Descriptor.
    Extracts feature descriptors for interest points in an image.

    Args:
        image: np.ndarray of the image.
        interest_points: (N, 2) array of interest points.
            The first row is the x-coordinates and the second row is the y-coordinates.
        output_base_name: the base name of the output path to save plots to.
        eps: small value to avoid dividing by 0 when bias/gain-normalizing feature descriptors.
        num_display: the number of feature descriptors to sample and display.

    Returns:
        feature_descriptors: (N, 64) array where each row is an interest point's flattened feature descriptor.
    """
    print("===== Extracting feature descriptors =====")

    if len(image.shape) == 3 and image.shape[2] == 3:
        bw_image = sk.color.rgb2gray(image)
    else:
        bw_image = image

    gaussian_kernel = make_2d_gaussian_kernel(sigma=4.5)
    smoothed = scipy.signal.convolve2d(bw_image, gaussian_kernel, mode="same")

    num_interest_points = interest_points.shape[0]  # (N, 2)
    patch_size = 40  # Extract 40x40 patches

    # Upstream harris_corner_detection function only finds interest_points
    # that are at least 20 pixels away from the edges, so a patch of [-20, +19]
    # around each interest point will always be in-bound.
    sample_offsets = np.arange(
        -patch_size // 2, patch_size // 2, 5
    )  # [-20, -15, ..., 15] with shape (8,)
    xs, ys = interest_points[:, 0], interest_points[:, 1]  # (N,)
    patch_xs = xs[:, None, None] + sample_offsets[None, None, :]  # (N, 1, 8)
    patch_ys = ys[:, None, None] + sample_offsets[None, :, None]  # (N, 8, 1)

    # Broadcast the 2 indices patch_xs, patch_ys into (N, 8, 8) --> fetch N (8, 8) patches from smoothed
    # Index into the smoothed image with row=patch_ys, col=patch_xs
    patches = smoothed[patch_ys, patch_xs]  # (N, 8, 8)
    patch_mean = np.mean(patches, axis=(1, 2), keepdims=True)
    patch_std = np.std(patches, axis=(1, 2), keepdims=True) + eps
    norm_patches = (patches - patch_mean) / patch_std

    # Randomly sample feature descriptor patches to visualize.
    rng = np.random.default_rng(seed=180)
    sample_idx = rng.choice(num_interest_points, size=num_display, replace=False)

    sampled_patches = norm_patches[sample_idx]
    nrows = math.ceil(num_display / 4) + 1
    ncols = 4

    fig, axs = plt.subplots(nrows, ncols)

    for i, ax in enumerate(axs.flatten()):
        if i >= num_display:
            ax.set_visible(False)
        else:
            ax.imshow(sampled_patches[i], cmap="gray")
            ax.set_title(f"Sample {i}")

    fig.suptitle(f"Sampled feature descriptors for {output_base_name}")
    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/{output_base_name}_feature_descriptors.jpg",
        bbox_inches="tight",
    )
    plt.show()

    # Flatten 8x8 patches into feature descriptor vectors.
    feature_descriptors = norm_patches.reshape((-1, 64))
    return feature_descriptors


def match_features(
    im1_fds: np.ndarray,
    im2_fds: np.ndarray,
    lowe_ratio_threshold: float = 0.4,
    verbose: bool = False,
):
    """
    Implements section 5 of the paper: Feature Matching.

    Args:
        im1_fds: (M, 64) array of feature descriptor vectors corresponding
            to image 1's interest points.
        im2_fds: (L, 64) array of feature descriptor vectors corresponding
            to image 2's interest points.
        lowe_ratio_threshold: threshold for accepting a neighbor as a match.
            Given the 2 nearest neighbors of a feature descriptor, only accept
            the closest neighbor as a match if the ratio of the
            squared distances 1-NN/2-NN <= threshold.
        verbose: whether or not to print informational progress.

    Returns:
        symmetric_matches: np.ndarray of shape (K, 2) where K is the number of
            feature matches found. Each element in the array is a tuple of feature
            descriptor indices (index_of_im1_feature_descriptor, index_of_im2_feature_descriptor).
            If no feature matches are found, symmetric_matches is an empy array of shape (0, 2)
    """
    print("===== Matching features =====")
    if verbose:
        print(
            f"Matching {im1_fds} feature descriptors from image 1 with {im2_fds} feature descriptors from image 2..."
        )

    # distances[i, j] is the squared distance from
    # image 1's ith feature descriptor to image 2's jth feature descriptor.
    distances = dist2(im1_fds, im2_fds)  # (M, L)

    # Top 2 closest neighbors in image 2 for each interest point from image 1
    # Find the bottom k using np.argpartition --> kth=1 puts 2nd smallest element in index 1,
    # and partitions all smaller elements before index 1. Then, indexing [:, :2] gets the
    # top 2 smallest distances.
    im1_nearest_neighbors = np.argpartition(distances, kth=1, axis=1)[:, :2]  # (M, 2)

    # Top 2 closest neighbors in image 1 for each interest point from image 2
    im2_nearest_neighbors = np.argpartition(distances, kth=1, axis=0)[:2, :].T  # (L, 2)

    matches_for_im1 = {}  # Maps index in im1 to index of matching feature descriptor from im2
    for i, closest_idxs in enumerate(im1_nearest_neighbors):
        j1, j2 = closest_idxs
        # Argpartition finds the indices of the 2 smallest distances but
        # does not gaurantee they are sorted.
        if distances[i, j1] < distances[i, j2]:
            nn1_idx = j1
            nn2_idx = j2
        else:
            nn1_idx = j2
            nn2_idx = j1

        d1, d2 = distances[i, nn1_idx], distances[i, nn2_idx]
        if d1 / d2 < lowe_ratio_threshold:
            matches_for_im1[i] = nn1_idx

    matches_for_im2 = {}  # Maps index in im2 to index of matching feature descriptor from im1
    for j, closest_idxs in enumerate(im2_nearest_neighbors):
        i1, i2 = closest_idxs
        # Argpartition finds the indices of the 2 smallest distances but
        # does not gaurantee they are sorted.
        if distances[i1, j] < distances[i2, j]:
            nn1_idx = i1
            nn2_idx = i2
        else:
            nn1_idx = i2
            nn2_idx = i1
        d1, d2 = distances[nn1_idx, j], distances[nn2_idx, j]
        if d1 / d2 < lowe_ratio_threshold:
            matches_for_im2[j] = nn1_idx

    # Save a pair of feature descriptors as a match if they are
    # both each other's closest match.
    symmetric_matches = []
    for i, j in matches_for_im1.items():
        if matches_for_im2.get(j) == i:
            symmetric_matches.append([i, j])

    if verbose:
        print(f"Found {len(symmetric_matches)} matches")

    # Preserve shape (K, 2) even if symmetric_matches is empty
    return np.array(symmetric_matches, dtype=int).reshape(-1, 2)


def plot_feature_matches(
    im1: np.ndarray,
    im2: np.ndarray,
    im1_output_base_name: str | None = None,
    im2_output_base_name: str | None = None,
):
    """
    Detects interest points and extracts feature descriptors for both images,
    then finds feature matches. Plots the found matches.
    """
    # corner_strengths is (N1,).
    # interest_points has shape (N1, 2), where the 1s column holds the xs and the 2nd column holds the ys
    im1_corner_strengths, im1_interest_points = harris_corner_detection(
        im1, output_base_name=im1_output_base_name
    )
    _, im1_anms_ips = adaptive_nonmaximal_suppression(
        im1,
        im1_corner_strengths,
        im1_interest_points,
        output_base_name=im1_output_base_name,
        verbose=True,
    )
    im1_fds = extract_feature_descriptors(
        im1, im1_anms_ips, output_base_name="im1", num_display=8
    )

    im2_corner_strengths, im2_interest_points = harris_corner_detection(
        im2, output_base_name=im2_output_base_name
    )
    _, im2_anms_ips = adaptive_nonmaximal_suppression(
        im2,
        im2_corner_strengths,
        im2_interest_points,
        output_base_name=im2_output_base_name,
        verbose=True,
    )
    im2_fds = extract_feature_descriptors(
        im2, im2_anms_ips, output_base_name="im2", num_display=8
    )

    feature_matches = match_features(im1_fds, im2_fds)  # (K, 2)

    im1_matched_points = im1_anms_ips[feature_matches[:, 0]]  # (K, 2)
    im1_matched_xs, im1_matched_ys = im1_matched_points[:, 0], im1_matched_points[:, 1]

    im2_matched_points = im2_anms_ips[feature_matches[:, 1]]  # (K, 2)
    im2_matched_xs, im2_matched_ys = im2_matched_points[:, 0], im2_matched_points[:, 1]

    num_matches = feature_matches.shape[0]
    colors = list(mcolors.XKCD_COLORS.keys())[:num_matches]

    fig, axs = plt.subplots(1, 2, figsize=(16, 6))

    axs[0].imshow(im1)
    axs[0].set_title(im1_output_base_name)
    axs[0].scatter(im1_matched_xs, im1_matched_ys, c=colors)

    axs[1].imshow(im2)
    axs[1].set_title(im2_output_base_name)
    axs[1].scatter(im2_matched_xs, im2_matched_ys, c=colors)

    fig.suptitle(
        f"Feature matches between {im1_output_base_name} and {im2_output_base_name}"
    )
    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/{im1_output_base_name}_{im2_output_base_name}_feature_matches.jpg",
        bbox_inches="tight",
    )
    plt.show()


def ransac(matches: np.ndarray, num_iters=500, eps=1, num_points=4):
    """
    4-point RANSAC algorithm for estimating robust homographies.
    The RANSAC algorithm reduces the impact of outliers on the final recovered homography.

    In pseuodocode:
        1. Select 4 feature pairs at random.
        2. Compute the homography H on the sampled feature pairs.
        3. Apply the candidate H to transform im1 to im2, then compute the number
            of inliers (how many points from im1 after transforming by H lie within
            a threshold of eps from the true matching point in im2).
        4. Repeat stpes 1-3, and keep the largest set of inliers.
        5. Re-compute a least-squares H estimate on the best set of kept inliers.

    Args:
        matches: (K, 2, 2) array of matching interest points between image 1 and image 2.
            K is the total number of correspondences, found from feature matches.
            Each element is a 2x2 matrix whose first column holds the (x, y)
            coordinates of a point from image 1, and whose second column holds the
            (x', y') coordinates of a point from image 2.
    """
    print("===== Improving homography with RANSAC =====")
    num_matches = matches.shape[0]

    # Extract im1's interest points from the first column of every 2x2 pair
    im1_ips = matches[:, :, 0]  # (K, 2)
    im2_ips = matches[
        :, :, 1
    ]  # Extract im2's interest points from the second column of every 2x2 pair

    im1_homogenous_ips = np.concat([im1_ips, np.ones((num_matches, 1))], axis=1)

    best_inliers_mask = np.ones(num_matches, dtype=bool)
    best_inliers_count = 0

    rng = np.random.default_rng(seed=180)
    for _ in range(num_iters):
        sample_idxs = rng.choice(
            num_matches, size=min(num_matches, num_points), replace=False
        )
        im1_points = im1_ips[sample_idxs]
        im2_points = im2_ips[sample_idxs]

        candidate_H = computeH(im1_points, im2_points)

        transformed_im1_homogeneous_ips, valid = normalize(
            candidate_H @ im1_homogenous_ips.T
        )  # (3, 3) x (3, K)

        valid = np.squeeze(
            valid.T
        )  # (1, N) --> (N,) for combining with boolean operators later

        # Extract just the (x, y) coordinates from the transformed points (which are in homogeneous coordinates)
        transformed_im1_ips = transformed_im1_homogeneous_ips[:2]  # (2, K)
        transformed_im1_ips = transformed_im1_ips.T  # (2, K) --> (K, 2)

        dist = np.linalg.norm(im2_ips - transformed_im1_ips, axis=-1)  # (K,)
        inliers_mask = valid & (dist < eps)
        curr_inliers_count = sum(inliers_mask)

        if curr_inliers_count > best_inliers_count:
            best_H = candidate_H
            best_inliers_mask = inliers_mask
            best_inliers_count = curr_inliers_count

    print(
        f"[RANSAC] Recomputing least-squares H estimate with {sum(best_inliers_mask)} inliers"
    )
    im1_inliers = im1_ips[best_inliers_mask]
    im2_inliers = im2_ips[best_inliers_mask]

    H = computeH(im1_inliers, im2_inliers)
    return H


def autostich_mosaic(images, image_base_names, output_base_name):
    """
    Automatically stich multiple images into a mosaic.

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
        image_base_names: list of strings, where the ith name corresponds to the ith input image.
        output_base_name: the base name of the output path to save plots to.
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

    # ips = interest points
    # fds = feature descriptors
    image_map = {}  # Maps image i to its interest points and feature_descriptors
    for i, (im, name) in enumerate(zip(images, image_base_names)):
        corner_strengths, interest_points = harris_corner_detection(
            im, output_base_name=name
        )

        _, anms_interest_points = adaptive_nonmaximal_suppression(
            im, corner_strengths, interest_points, output_base_name=name
        )

        feature_descriptors = extract_feature_descriptors(
            im, anms_interest_points, output_base_name=name
        )
        image_map[i] = {
            "interest_points": anms_interest_points,  # (N, 2)
            "feature_descriptors": feature_descriptors,  # (N, 64)
        }

    homographies = []  # homographies[i] is the transform that maps im_{i} to im_{i+1}
    for i in range(num_images - 1):
        im1_interest_points = image_map[i]["interest_points"]
        im1_feature_descriptors = image_map[i]["feature_descriptors"]

        im2_interest_points = image_map[i + 1]["interest_points"]
        im2_feature_descriptors = image_map[i + 1]["feature_descriptors"]

        feature_matches = match_features(
            im1_feature_descriptors, im2_feature_descriptors
        )

        im1_matched_points = im1_interest_points[feature_matches[:, 0]]  # (K, 2)

        im1_matched_xs, im1_matched_ys = (
            im1_matched_points[:, 0],
            im1_matched_points[:, 1],
        )

        im2_matched_points = im2_interest_points[feature_matches[:, 1]]  # (K, 2)
        im2_matched_xs, im2_matched_ys = (
            im2_matched_points[:, 0],
            im2_matched_points[:, 1],
        )

        num_matches = feature_matches.shape[0]

        # If there are more matches than the number of colors,
        # repeat colors to have at least num_matches items before slicing
        colors = list(mcolors.XKCD_COLORS.keys())
        colors = colors * math.ceil(num_matches / len(colors))
        colors = colors[:num_matches]

        fig, axs = plt.subplots(1, 2, figsize=(16, 6))

        axs[0].imshow(images[i])
        axs[0].set_title(image_base_names[i])
        axs[0].scatter(im1_matched_xs, im1_matched_ys, c=colors)

        axs[1].imshow(images[i + 1])
        axs[1].set_title(image_base_names[i + 1])
        axs[1].scatter(im2_matched_xs, im2_matched_ys, c=colors)

        fig.suptitle(
            f"{num_matches} feature matches between {image_base_names[i]} and {image_base_names[i + 1]}"
        )
        plt.tight_layout()
        plt.savefig(
            f"{OUTPUT_DIR}/{image_base_names[i]}_{image_base_names[i + 1]}_feature_matches.jpg",
            bbox_inches="tight",
        )
        plt.show()

        matches = np.stack([im1_matched_points, im2_matched_points], axis=2)
        H_im1_to_im2 = ransac(matches)
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
    fig.suptitle(f"Auto-stitched mosaic of {output_base_name}")
    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/{output_base_name}_mosaic_plots.jpg",
        bbox_inches="tight",
    )
    plt.show()

    plt.imshow(mosaic)
    plt.show()

    mosaic_saved = (mosaic * 255.0).astype(np.uint8)
    sk.io.imsave(f"{OUTPUT_DIR}/{output_base_name}_autostitch_mosaic.jpg", mosaic_saved)
    print(f"Saved image to {OUTPUT_DIR}/{output_base_name}_autostitch_mosaic.jpg")

    return mosaic


def main():
    print("===== (Auto)stitching and Photo Mosaics =====")
    # Section A.2: Recover Homographies
    gec_1 = img_to_np(DATA_DIR / "gec_1.jpg")
    gec_2 = img_to_np(DATA_DIR / "gec_2.jpg")
    gec_3 = img_to_np(DATA_DIR / "gec_3.jpg")

    # gec_1_pts, gec_2_pts = get_correspondences(gec_1, gec_2, num_correspondences=8, output_base_name="gec_1_2")
    # H = computeH(gec_1_pts, gec_2_pts, verbose=True)

    # Section A.3: Warp the Images (rectification)
    # painting_im = img_to_np(DATA_DIR / "painting.jpg")
    # rectify(painting_im, output_base_name="painting")

    # pompeii_im = img_to_np(DATA_DIR / "pompeii.jpg")
    # rectify(pompeii_im, output_base_name="pompeii")

    # wall_fresco_im = img_to_np(DATA_DIR / "wall_fresco.jpg")
    # rectify(wall_fresco_im, output_base_name="wall_fresco")

    # # Section A.4: Blend the Images into a Mosaic
    # gec_1 = img_to_np(DATA_DIR / "gec_1.jpg")
    # gec_2 = img_to_np(DATA_DIR / "gec_2.jpg")
    # gec_3 = img_to_np(DATA_DIR / "gec_3.jpg")

    # make_mosaic(
    #     [gec_1, gec_2, gec_3],
    #     "gec",
    #     6,
    # )

    campus_1 = img_to_np(DATA_DIR / "campus_1.jpg")
    campus_2 = img_to_np(DATA_DIR / "campus_2.jpg")
    campus_3 = img_to_np(DATA_DIR / "campus_3.jpg")
    campus_4 = img_to_np(DATA_DIR / "campus_4.jpg")
    campus_5 = img_to_np(DATA_DIR / "campus_5.jpg")

    # make_mosaic(
    #     [campus_1, campus_2, campus_3, campus_4, campus_5],
    #     "campus",
    #     6,
    # )

    kresge_1 = img_to_np(DATA_DIR / "kresge_1.jpg")
    kresge_2 = img_to_np(DATA_DIR / "kresge_2.jpg")
    kresge_3 = img_to_np(DATA_DIR / "kresge_3.jpg")
    kresge_4 = img_to_np(DATA_DIR / "kresge_4.jpg")
    kresge_5 = img_to_np(DATA_DIR / "kresge_5.jpg")

    # make_mosaic(
    #     [kresge_1, kresge_2, kresge_3, kresge_4, kresge_5],
    #     "kresge",
    #     6,
    # )

    # # Section B.1: Harris Corner Detection
    # print("\nSection B.1: Harris Corner Detection\n")
    # gec_1_h, gec_1_ips = harris_corner_detection(image=gec_1, output_base_name="gec_1")

    # _, gec_1_anms_ips = adaptive_nonmaximal_suppression(
    #     image=gec_1,
    #     corner_strengths=gec_1_h,
    #     interest_points=gec_1_ips,
    #     n_ip=500,
    #     c_robust=0.9,
    #     output_base_name="gec_1",
    #     plot_comparison=True,
    #     verbose=True,
    # )

    # Section B.2: Feature Descriptor Extraction
    # print("\nSection B.2: Feature Descriptor Extraction\n")
    # gec_1_fds = extract_feature_descriptors(
    #     image=gec_1, interest_points=gec_1_anms_ips, output_base_name="gec_1", eps=1e-8, num_display=8
    # )

    # gec_2_h, gec_2_ips = harris_corner_detection(gec_2, output_base_name="gec_2")
    # _, gec_2_anms_ips = adaptive_nonmaximal_suppression(
    #     image=gec_2,
    #     corner_strengths=gec_2_h,
    #     interest_points=gec_2_ips,
    #     n_ip=500,
    #     c_robust=0.9,
    #     output_base_name="gec_2",
    #     plot_comparison=True,
    #     verbose=True,
    # )
    # gec_2_fds = extract_feature_descriptors(
    #     image=gec_2, interest_points=gec_2_anms_ips, output_base_name="gec_2",  eps=1e-8, num_display=8
    # )

    # Section B.3: Feature Matching
    # print("\nSection B.3: Feature Matching\n")
    # plot_feature_matches(
    #     im1=gec_2, im2=gec_3, im1_output_base_name="gec_2", im2_output_base_name="gec_3"
    # )
    # plot_feature_matches(
    #     im1=campus_4,
    #     im2=campus_5,
    #     im1_output_base_name="campus_4",
    #     im2_output_base_name="campus_5",
    # )
    # plot_feature_matches(
    #     im1=kresge_3,
    #     im2=kresge_4,
    #     im1_output_base_name="kresge_3",
    #     im2_output_base_name="kresge_4",
    # )

    # # Section B.4: RANSAC for Robust Homography
    # print("\nSection B.4: RANSAC for Robust Homography\n")
    # im1_matched_points = gec_1_ips[feature_matches[:, 0]]  # (K, 2)
    # im2_matched_points = gec_2_ips[feature_matches[:, 1]]  # (K, 2)

    # matches = np.stack([im1_matched_points, im2_matched_points], axis=2)
    # H = ransac(matches)
    # print(f"H recoverd with RANSAC:\n{H}")

    # Full auto-stitching mosaic-making pipeline
    print("\nThe Full Auto-Stitching Mosaic-Making Pipeline\n")
    autostich_mosaic(
        images=[gec_1, gec_2, gec_3],
        image_base_names=["gec_1", "gec_2", "gec_3"],
        output_base_name="gec",
    )

    autostich_mosaic(
        images=[campus_1, campus_2, campus_3, campus_4, campus_5],
        image_base_names=["campus_1", "campus_2", "campus_3", "campus_4", "campus_5"],
        output_base_name="campus",
    )

    autostich_mosaic(
        images=[kresge_1, kresge_2, kresge_3, kresge_4, kresge_5],
        image_base_names=["kresge_1", "kresge_2", "kresge_3", "kresge_4", "kresge_5"],
        output_base_name="kresge",
    )


if __name__ == "__main__":
    main()
