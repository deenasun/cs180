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

    x_min, x_max, y_min, y_max = get_warped_corners(im, H)

    h_out = y_max - y_min + 1
    w_out = x_max - x_min + 1

    # Top-left pixel in out (matrix index (0, 0)) corresponds
    # to the pixel location (x_min, y_min) in the warped image.
    if im.ndim == 3:
        out = np.zeros((h_out, w_out, c_in))
    else:
        out = np.zeros((h_out, w_out, 1))

    # 2D mask to mark which pixels in the output had valid source mappings.
    # Used as alpha channel later to distinguish output pixel = 0 because
    # it came from a 0 pixel in the source vs. output pixel = 0 because it
    # had no valid source mapping.
    mask = np.zeros((h_out, w_out, 1)).astype(bool)

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

    return out, mask, (x_min, x_max, y_min, y_max)


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

    x_min, x_max, y_min, y_max = get_warped_corners(im, H)

    h_out = y_max - y_min + 1
    w_out = x_max - x_min + 1

    # Top-left pixel in out (matrix index (0, 0)) corresponds
    # to the pixel location (x_min, y_min) in the warped image.
    # Top-left pixel in out (matrix index (0, 0)) corresponds
    # to the pixel location (x_min, y_min) in the warped image.
    if im.ndim == 3:
        out = np.zeros((h_out, w_out, c_in))
    else:
        out = np.zeros((h_out, w_out, 1))

    # 2D mask to mark which pixels in the output had valid source mappings.
    # Used as alpha channel later to distinguish output pixel = 0 because
    # it came from a 0 pixel in the source vs. output pixel = 0 because it
    # had no valid source mapping.
    mask = np.zeros((h_out, w_out, 1)).astype(bool)

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

    return out, mask, (x_min, x_max, y_min, y_max)


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

    return x_min, x_max, y_min, y_max


def gaussian_stack(
    im=None,
    max_levels=2,
):
    """
    Build a Gaussian stack of im.
    """

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


def make_3image_mosaic(
    left_im: np.ndarray, center_im: np.ndarray, right_im: np.ndarray
):
    """
    Create a mosaic by stitching together 3 images corresponding to a rotation from left -> center -> right.

    Treats the center images as the reference, computes homographies from left_im and right_im to center_im,
    places center_im in the center of a shared view, and transforms the left_im and right_im onto the shared projective view.

    To smoothly blend the images in the mosaic together, each image and its mask are first projected onto their own copies
    of the projective view. Then, each canvas containing the warped image is turned into a Laplacian stack
    and each canvas containing the warped image's mask is turned into a Gaussian stack. Finally, each level of the Laplacian stack
    are collapsed together, with each Laplacian weighted by its mask's Gaussian.

    Args:
        left_im: np.ndarray of the left image
        center_im: np.ndarray of the left image
        right_im: np.ndarray of the left image

    Returns:
        mosaic: np.ndarray of the final mosaic

    Also creates a plot of the input images alongside the final mosaic, and saves both
    the plot and the final mosaic to OUTPUT_DIR.
    """
    h_center, w_center = center_im.shape[:2]
    left_im_pts, center_im_pts = get_correspondences(
        left_im, center_im, num_correspondences=8
    )
    left_to_center_H = computeH(left_im_pts, center_im_pts)
    out_left, mask_left, corners_left = warpImageBilinear(left_im, left_to_center_H)
    x_min_left, x_max_left, y_min_left, y_max_left = corners_left

    right_im_pts, center_im_pts = get_correspondences(
        right_im, center_im, num_correspondences=8
    )
    right_to_center_H = computeH(right_im_pts, center_im_pts)
    out_right, mask_right, corners_right = warpImageBilinear(
        right_im, right_to_center_H
    )
    x_min_right, x_max_right, y_min_right, y_max_right = corners_right

    # Compute dimensions of shared canvas
    x_min = math.floor(min(x_min_left, 0, x_min_right))
    x_max = math.ceil(max(x_max_left, w_center - 1, x_max_right))
    y_min = math.floor(min(y_min_left, 0, y_min_right))
    y_max = math.ceil(max(y_max_left, h_center - 1, y_max_right))

    canvas_w = x_max - x_min + 1
    canvas_h = y_max - y_min + 1

    # B's top-left pixel (0, 0) should be placed at row -y_min, col -x_min in the canvas
    # Center image's top-left pixel (0, 0) should be placed at row -y_min, col -x_min in the canvas
    canvas = np.zeros((canvas_h, canvas_w, 3))
    # Binary mask that is an additive sum of all the warped image's masks.
    # Used as a final mask to crop out any blurry halos in the final canvas around the final mosaic
    # that result from the gaussian weights blurring outer pixels into neighboring pixels on the canvas.
    final_binary_mask = np.zeros((canvas_h, canvas_w, 3))

    # Create 6 canvases, each contains one of the 3 images or one of the masks
    canvas_left, canvas_center, canvas_right = (
        canvas.copy(),
        canvas.copy(),
        canvas.copy(),
    )

    canvas_mask_left, canvas_mask_center, canvas_mask_right = (
        canvas.copy(),
        canvas.copy(),
        canvas.copy(),
    )

    canvas_left[
        y_min_left - y_min : y_max_left - y_min + 1,
        x_min_left - x_min : x_max_left - x_min + 1,
    ] = out_left
    canvas_mask_left[
        y_min_left - y_min : y_max_left - y_min + 1,
        x_min_left - x_min : x_max_left - x_min + 1,
        :,
    ] = mask_left.astype(float)
    final_binary_mask += canvas_mask_left

    canvas_center[-y_min : -y_min + h_center, -x_min : -x_min + w_center] = center_im
    mask_center = np.ones((h_center, w_center, 1), dtype=float)
    canvas_mask_center[-y_min : -y_min + h_center, -x_min : -x_min + w_center, :] = (
        mask_center.astype(float)
    )
    final_binary_mask += canvas_mask_center

    canvas_right[
        y_min_right - y_min : y_max_right - y_min + 1,
        x_min_right - x_min : x_max_right - x_min + 1,
    ] = out_right
    canvas_mask_right[
        y_min_right - y_min : y_max_right - y_min + 1,
        x_min_right - x_min : x_max_right - x_min + 1,
        :,
    ] = mask_right.astype(float)
    final_binary_mask += canvas_mask_right

    stack_depth = 2
    laplacian_left = laplacian_stack(canvas_left, stack_depth)  # (N, H, W, 3)
    laplacian_center = laplacian_stack(canvas_center, stack_depth)
    laplacian_right = laplacian_stack(canvas_right, stack_depth)
    laplacian_stacks = np.stack(
        [laplacian_left, laplacian_center, laplacian_right], axis=1
    )

    gaussian_mask_left = gaussian_stack(canvas_mask_left, stack_depth)
    gaussian_mask_center = gaussian_stack(canvas_mask_center, stack_depth)
    gaussian_mask_right = gaussian_stack(canvas_mask_right, stack_depth)
    gaussian_mask_stacks = np.stack(
        [gaussian_mask_left, gaussian_mask_center, gaussian_mask_right], axis=1
    )

    mosaic = np.zeros_like(canvas)
    for laplacians, gaussians in zip(laplacian_stacks, gaussian_mask_stacks):
        blend = (
            gaussians[0] * laplacians[0]
            + gaussians[1] * laplacians[1]
            + gaussians[2] * laplacians[2]
        )
        gaussian_weights = gaussians[0] + gaussians[1] + gaussians[2]
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

    fig, axs = plt.subplots(2, 3, figsize=(4 * len(laplacian_stacks), 6))

    axs[0, 0].imshow(left_im)
    axs[0, 1].imshow(center_im)
    axs[0, 2].imshow(right_im)
    axs[1, 1].imshow(mosaic)

    axs[1, 0].set_visible(False)
    axs[1, 2].set_visible(False)

    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/mosaic_plots.jpg",
        bbox_inches="tight",
    )
    plt.show()

    plt.imshow(mosaic)
    plt.show()

    mosaic_saved = (mosaic * 255.0).astype(np.uint8)
    sk.io.imsave(f"{OUTPUT_DIR}/mosaic.jpg", mosaic_saved)
    print(f"Saved image to {f'{OUTPUT_DIR}/mosaic.jpg'}")

    return mosaic


def make_mosaic(images: list[np.ndarray], center_image_idx: int):
    """
    Create a mosaic by stitching together multiple images.

    Treats the image located at `center_image_idx` as the reference: all homographies therefore compute an H
    that will warp the other images to match center_im's projective plane.

    To smoothly blend the images in the mosaic together, each image and its mask are first projected onto their own copies
    of the projective view. Then, each canvas containing the warped image is turned into a Laplacian stack
    and each canvas containing the warped image's mask is turned into a Gaussian stack. Finally, each level of the Laplacian stack
    are collapsed together, with each Laplacian weighted by its mask's Gaussian.

    Args:
        images: list of np.ndarrays
        center_image_idx: integer index of the image that should be placed at the center of the shared projective plane.

    Returns:
        mosaic: np.ndarray of the final mosaic

    Also creates a plot of the input images alongside the final mosaic, and saves both
    the plot and the final mosaic to OUTPUT_DIR.
    """
    num_images = len(images)
    center_im = images[center_image_idx]
    h_center, w_center = center_im.shape[:2]

    idx_to_warped = {}  # Maps image idx to (out, mask, corners)
    x_mins = []
    x_maxes = []
    y_mins = []
    y_maxes = []
    for idx, im in enumerate(images):
        if idx == center_image_idx:
            continue
        im2_pts, center_im_pts = get_correspondences(
            im, center_im, num_correspondences=8
        )

        im2_to_center_H = computeH(im2_pts, center_im_pts)
        out, mask, corners = warpImageBilinear(im, im2_to_center_H)
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

        if idx != center_image_idx:
            out = idx_to_warped[idx]["out"]
            mask = idx_to_warped[idx]["mask"]
            x_min, x_max, y_min, y_max = idx_to_warped[idx]["corners"]
            # Each image's top-left pixels should get translated to y_min - y_min_canvas, x_min - x_min_canvas
            # in the final shared canvas after being warped
            curr_canvas[
                y_min - y_min_canvas : y_max - y_min_canvas + 1,
                x_min - x_min_canvas : x_max - x_min_canvas + 1,
            ] = out

            curr_canvas_mask[
                y_min - y_min_canvas : y_max - y_min_canvas + 1,
                x_min - x_min_canvas : x_max - x_min_canvas + 1,
            ] = mask.astype(float)
        else:
            # Center image's top-left pixel (0, 0) should be placed at row -y_min_canvas, col -x_min_canvas in the canvas
            curr_canvas[
                -y_min_canvas : -y_min_canvas + h_center,
                -x_min_canvas : -x_min_canvas + w_center,
            ] = center_im
            mask_center = np.ones((h_center, w_center, 1), dtype=float)
            curr_canvas_mask[
                -y_min_canvas : -y_min_canvas + h_center,
                -x_min_canvas : -x_min_canvas + w_center,
                :,
            ] = mask_center.astype(float)

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
    height_ratios = list(np.ones(num_rows - 1)) + [2]
    fig, axs = plt.subplots(
        num_rows,
        num_cols,
        figsize=(4 * num_cols, 3 * num_rows),
        gridspec_kw={"height_ratios": height_ratios},
    )

    for idx, ax in enumerate(axs.flatten()):
        if idx >= len(images):
            ax.set_visible(False)
        else:
            ax.imshow(images[idx])
            ax.set_title(
                f"Image {idx + 1}{' (reference)' if idx == center_image_idx else ''}"
            )

    axs[-1, num_cols // 2].set_visible(True)
    axs[-1, num_cols // 2].imshow(mosaic)

    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/mosaic_plots.jpg",
        bbox_inches="tight",
    )
    plt.show()

    plt.imshow(mosaic)
    plt.show()

    mosaic_saved = (mosaic * 255.0).astype(np.uint8)
    sk.io.imsave(f"{OUTPUT_DIR}/mosaic.jpg", mosaic_saved)
    print(f"Saved image to {f'{OUTPUT_DIR}/mosaic.jpg'}")

    return mosaic


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

    # warp_im1 = img_to_np(DATA_DIR / "parthenon.jpg")
    # h, w, _ = warp_im1.shape
    # warp_im2 = np.zeros_like(warp_im1)
    # size_of_corner = max(h // 15, w // 15)
    # warp_im2[
    #     h // 2 - size_of_corner : h // 2 + size_of_corner,
    #     w // 2 - size_of_corner : w // 2 + size_of_corner,
    #     :,
    # ] = 1

    # warp_im1_pts, warp_im2_pts = get_correspondences(warp_im1, warp_im2)

    # warp_H = computeH(warp_im1_pts, warp_im2_pts)

    # print(f"Recovered homography matrix: {warp_H}")

    # nn_warp, _, _ = warpImageNearestNeighbor(warp_im1, warp_H)

    # bilinear_warp, _, _ = warpImageBilinear(warp_im1, warp_H)

    # fig, axs = plt.subplots(1, 2, figsize=(12, 6))
    # axs[0].imshow(nn_warp)
    # axs[0].set_title("Warp (nearest neighbors inverse warp)")

    # axs[1].imshow(bilinear_warp)
    # axs[1].set_title("Warp (bilinear interpolation inverse warp)")

    # plt.tight_layout()
    # plt.show()

    mosaic_left_im = img_to_np(DATA_DIR / "gec_1.jpg")
    mosaic_center_im = img_to_np(DATA_DIR / "gec_2.jpg")
    mosaic_right_im = img_to_np(DATA_DIR / "gec_3.jpg")

    mosaic = make_mosaic([mosaic_left_im, mosaic_center_im, mosaic_right_im], 1)


if __name__ == "__main__":
    main()
