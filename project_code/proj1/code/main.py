# CS180 (CS280A): Project 1
import time
import numpy as np
import skimage as sk
import skimage.io as skio
import matplotlib.pyplot as plt
from pathlib import Path

DATA_DIR = "data/"
OUTPUT_DIR = "out/"

# name of the input file
input_file = "monastery"
input_file_extension = ".jpg"

# read in the image
im = skio.imread(DATA_DIR + input_file + input_file_extension)
plt.imshow(im, cmap="gray")

# print(im.dtype)  # dtype: unit8

# convert to double (might want to do this later on to save memory)
im = sk.img_as_float(im)

# print(im.dtype)  # dtype: float64

width = im.shape[1]
# compute the height of each part (just 1/3 of total)
# NOTE: need to use uint64 because uint8 is [0, 255] and any value
height = np.floor(im.shape[0] / 3.0).astype(np.uint64)

print(f"{input_file}{input_file_extension} has dimensions {height} x {width} (h x w)")

# separate color channels
# NOTE: each glass plate image in the data folder is in BGR order
b = im[:height]
g = im[height : 2 * height]
r = im[2 * height : 3 * height]

# stack color channels into original image
orig_im = np.dstack([r, g, b])


def find_colored_edges(img, color_val=1.0, limit=0.05):
    h, w = img.shape

    # Stop once most of the pixels in this edge is no longer the target color
    # E.g. if color_val = 1.0 (white), then if the abs diff between this
    # pixel and white is less than 1e-1, this pixel is most likely also white
    # Break once fraction of pixels with the target color falls below 0.7
    left_edge = 0
    while left_edge < int(limit * w):
        if np.mean(np.abs(color_val - img[:, left_edge]) <= 1e-1) < 0.7:
            break
        left_edge += 1

    # Stop once most of the right edge's pixels are longer the target color
    right_edge = w - 1
    while right_edge > int((1.0 - limit) * w):
        if np.mean(np.abs(color_val - img[:, right_edge]) <= 1e-1) < 0.7:
            break
        right_edge -= 1

    # Stop once most of the right edge's pixels are longer the target color
    top_edge = 0
    while top_edge < int(limit * h):
        if np.mean(np.abs(color_val - img[top_edge, :]) <= 1e-1) < 0.7:
            break
        top_edge += 1

    # Stop once most of the right edge's pixels are longer the target color
    bottom_edge = h - 1
    while bottom_edge > int((1.0 - limit) * h):
        if np.mean(np.abs(color_val - img[bottom_edge, :]) <= 1e-1) < 0.7:
            break
        bottom_edge -= 1

    return left_edge, right_edge, top_edge, bottom_edge
    # return int(0.1 * w), int(0.9 * w), int(0.1 * h), int(0.9 * h)


def crop_rgb(r, g, b, color_val=1.0):
    r_left, r_right, r_top, r_bottom = find_colored_edges(r, color_val=color_val)
    g_left, g_right, g_top, g_bottom = find_colored_edges(g, color_val=color_val)
    b_left, b_right, b_top, b_bottom = find_colored_edges(b, color_val=color_val)

    # Determine shared border crop to use for all 3 plates
    # so that their original coordinates are preserved and they all have the same shape
    shared_left = max(r_left, g_left, b_left)  # Largest (innermost) left boundary
    shared_right = min(r_right, g_right, b_right)  # Smallest (innermost) right boundary
    shared_top = max(r_top, g_top, b_top)  # Largest (innermost) top boundary
    shared_bottom = min(
        r_bottom, g_bottom, b_bottom
    )  # Smallest (innermost) bottom boundary

    r_crop = r[shared_top : shared_bottom + 1, shared_left : shared_right + 1]
    g_crop = g[shared_top : shared_bottom + 1, shared_left : shared_right + 1]
    b_crop = b[shared_top : shared_bottom + 1, shared_left : shared_right + 1]

    return r_crop, g_crop, b_crop


crop_white_r, crop_white_g, crop_white_b = crop_rgb(r, g, b, color_val=1.0)
crop_black_r, crop_black_g, crop_black_b = crop_rgb(
    crop_white_r, crop_white_g, crop_white_b, color_val=0.1
)

cropped_r, cropped_g, cropped_b = crop_black_r, crop_black_g, crop_black_b

# plt.imshow(cropped_r)
# plt.imshow(cropped_g)
# plt.imshow(cropped_b)


class ShapeMismatchError(Exception):
    """Raised when two matrices have incompatible shapes"""


class InvalidArgumentError(Exception):
    """Raised when an unrecognized argument is passed to a function"""


class AlignmentError(Exception):
    """Raised for catch-all image alignment errors"""


def l2_distance(mat1: np.ndarray, mat2: np.ndarray):
    """
    Returns the L2 norm of the difference between 2 matrices (Euclidean distance)

    || mat1 - mat2 || = sqrt(sum(mat1 - mat2)^2) where the difference is taken element-wise
    """
    if not np.equal(mat1.shape, mat2.shape).all():
        raise ShapeMismatchError(
            f"the shapes of mat1 and mat2 don't match: mat1.shape {mat1.shape}, mat2.shape {mat2.shape}"
        )

    return np.sqrt(np.sum((mat1 - mat2) ** 2))


def normalized_cross_correlation(mat1: np.ndarray, mat2: np.ndarray):
    """
    Returns the NCC: a dot product between two mean-subtracted, normalized vectors
    ((image1-mean(image1))./||image1-mean(image1)|| and (image2-mean(image2))./||image2-mean(image2)||)
    """
    mean1 = mat1.mean()  # scalar
    norm1 = (mat1 - mean1) / np.sqrt(np.sum((mat1 - mean1) ** 2))

    mean2 = mat2.mean()  # scalar
    norm2 = (mat2 - mean2) / np.sqrt(np.sum((mat2 - mean2) ** 2))

    return np.dot(norm1.ravel(), norm2.ravel())


# align the images
# functions that might be useful for aligning the images include:
# np.roll, np.sum, sk.transform.rescale (for multiscale)
def align(img, base_img, metric="l2", y_radius=15, x_radius=15, verbose=True):
    """Align img to the base_img.

    Displacements (dy, dx) are calculated based on the assumption that the origin (0, 0)
    refers to the top left corner of the matrix/image.

    Positive dy shifts downward, positive dx shifts rightward.

    Args:
        img: np.ndarray
        base_img: the base image to align img to
        metric: "l2" or "ncc" - whether to score alignment
            by minimizing L2 distance or maximizing NCC
        y_radius: algo will search for best vertical displacement between [-y_radius, +y_radius]
        x_radius: algo will search for best horizontal displacement between [-x_radius, +x_radius]
        verbose: bool

    Returns:
        best_dy: number of pixels to displace in the y-direction
            to achieve the best alignment metric between img and base_img
        best_dx: number of pixels to displace in the x-direction
            to achieve the best alignment metric between img and base_img

    Raises:
        InvalidArgumentError: If metric is not L2 distance or Normalized Cross Correlation
    """
    if metric != "l2" and metric != "ncc":
        raise InvalidArgumentError("metric should be either l2 or ncc")

    if y_radius <= 0:
        raise InvalidArgumentError("y_radius must be a positive integer")
    if x_radius <= 0:
        raise InvalidArgumentError("x_radius must be a positive integer")

    best_dy, best_dx = 0, 0
    best_metric = np.inf if metric == "l2" else -np.inf

    # Score only the center of the base image and the candidate displacements.
    # np.roll wraps pixels to the opposite edge, so the glass-plate borders
    # can dominate the scoring metrics if not excluded.
    h, w = base_img.shape

    if y_radius >= h // 2:
        raise InvalidArgumentError(
            f"search y_radius is too big for an image of dimensions {h, w}. y_radius must be at most {h // 2}"
        )

    if x_radius >= w // 2:
        raise InvalidArgumentError(
            f"search x_radius is too big for an image of dimensions {h, w}. x_radius must be at most {w // 2}"
        )
    trim_edges = max(int(np.round(0.05 * min(h, w))), 15)
    trimmed_base = base_img[trim_edges:-trim_edges, trim_edges:-trim_edges]

    for dy in np.arange(-y_radius, y_radius + 1):
        for dx in np.arange(-x_radius, x_radius + 1):
            rolled = np.roll(img, shift=(dy, dx), axis=(0, 1))

            # Crop to a core interior for the candidate displacement
            candidate = rolled[trim_edges:-trim_edges, trim_edges:-trim_edges]

            if metric == "l2":
                dist = l2_distance(candidate, trimmed_base)
                if dist < best_metric:
                    best_metric = dist
                    best_dy, best_dx = dy, dx

            else:
                corr = normalized_cross_correlation(candidate, trimmed_base)
                if corr > best_metric:
                    best_metric = corr
                    best_dy, best_dx = dy, dx

    if verbose:
        print(f"Best metric found: {best_metric}")
        print(f"Displacement vector (dy, dx): {best_dy, best_dx}")
    return best_dy, best_dx


def search(
    mat, base_mat, dy_center, dx_center, dy_radius, dx_radius, metric="l2", margin=0
):
    """Search a radius around an estimate, and return the displacements that optimize the alignment metric

    Args:
        mat: 2-dimensional np.ndarray
        base_mat: 2-dimensional np.ndarray to align mat to
        dy_center: current estimate for the displacement in the y-direction
        dx_center: current estimate for the displacement in the x-direction
        dy_radius: the radius around dy_center to search in order to find a better y displacement
        dx_radius: the radius around dx_center to search in order to find a better x displacement
        metric: "l2" or "ncc"
        margin: extra margin around the edges to ignore

    Returns:
        best_dy: number of pixels to displace in the y-direction
            to achieve the best alignment metric between mat and base_mat
        best_dx: number of pixels to displace in the x-direction
            to achieve the best alignment metric between mat and base_mat
        best_metric: the best value for the metric found during search
    """
    h, w = base_mat.shape

    best_dy, best_dx = dy_center, dx_center
    best_metric = np.inf if metric == "l2" else -np.inf

    dy_min, dy_max = dy_center - dy_radius, dy_center + dy_radius
    dx_min, dx_max = dx_center - dx_radius, dx_center + dx_radius

    # Coordinates of a fixed interior rectangle from the base image
    # to compare all candidates to
    y0 = max(margin, margin + dy_max)  # top edge
    y1 = min(h - margin, h - margin + dy_min)  # bottom edge
    x0 = max(margin, margin + dx_max)  # left edge
    x1 = min(w - margin, w - margin + dx_min)  # right edge

    if y1 <= y0 or x1 <= x0:
        raise AlignmentError(
            f"Invalid bounds for the base image's fixed interior rectangle: {y0, y1, x0, x1} (y0, y1, x0, x1)"
        )

    base_rect = base_mat[y0:y1, x0:x1]

    for dy in np.arange(dy_min, dy_max + 1):
        for dx in np.arange(dx_min, dx_max + 1):
            # Extract the cells from mat that are now placed on top of the
            # fixed rectangle from the base image after mat is displaced by (dy, dx)
            candidate = mat[y0 - dy : y1 - dy, x0 - dx : x1 - dx]

            if metric == "l2":
                dist = l2_distance(candidate, base_rect)
                if dist < best_metric:
                    best_metric = dist
                    best_dy, best_dx = dy, dx
            else:
                corr = normalized_cross_correlation(candidate, base_rect)
                if corr > best_metric:
                    best_metric = corr
                    best_dy, best_dx = dy, dx

    return best_dy, best_dx, best_metric


def pyramid_align(img, base_img, metric="l2", radius=8, margin=2, verbose=False):
    """Recursive image pyramid implementation to align img to base_img.

    Args:
        img: 2-dimensional np.ndarray representing a single glass plate (usually R or G)
        base_img: 2-dimensional np.ndarray representing a single glass plate (usually B)
        metric: "l2" or "ncc"
        radius: the range of values to search around the best estimate (dy, dx)
            returned by the recursive call.
        margin: extra margin around the edges to ignore

    Returns:
        dy: best estimate for the number of pixels to displace in the y-direction
            at this image resolution
        dx: best estimate for the number of pixels to displace in the x-direction
            at this image resolution
    """
    if metric != "l2" and metric != "ncc":
        raise InvalidArgumentError("metric should be either l2 or ncc")

    h, w = img.shape

    # Base case: if h <= 200 or w <= 200, perform more exhaustive search
    if h <= 200 or w <= 200:
        best_dy, best_dx, _ = search(
            img,
            base_img,
            dy_center=0,
            dx_center=0,
            dy_radius=16,
            dx_radius=16,
            metric=metric,
            margin=2,
        )
        if verbose:
            print(
                f"[BASE CASE] image shape: (h, w) {h, w}, best displacement: {best_dy, best_dx}"
            )
        return best_dy, best_dx

    downsampled = sk.transform.rescale(img, 0.5, anti_aliasing=True)
    downsampled_base = sk.transform.rescale(base_img, 0.5, anti_aliasing=True)
    recursive_dy, recursive_dx = pyramid_align(
        downsampled,
        downsampled_base,
        metric=metric,
        radius=radius,
        margin=margin,
        verbose=verbose,
    )

    # Scale displacement estimates from recursive call
    # because those dx, dy represented the pixel shifts needed for an image
    # with 1/2 the number of pixels as the current image
    best_dy, best_dx = 2 * recursive_dy, 2 * recursive_dx
    best_metric = np.inf if metric == "l2" else -np.inf

    # Search a small neighborhood around the scaled estimates for dy, dx
    best_dy, best_dx, best_metric = search(
        img,
        base_img,
        dy_center=best_dy,
        dx_center=best_dx,
        dy_radius=radius,
        dx_radius=radius,
        metric=metric,
        margin=margin,
    )

    if verbose:
        print(f"Current image resolution: {img.shape}")
        print(f"Best metric found: {best_metric}")
        print(f"Displacement vector (dy, dx): {best_dy, best_dx}")
    return best_dy, best_dx


# Single-scale, basic align
dy_r, dx_r = align(r, b, "l2")
ar = np.roll(r, shift=(dy_r, dx_r), axis=(0, 1))

dy_g, dx_g = align(g, b, "l2")
ag = np.roll(g, shift=(dy_r, dx_r), axis=(0, 1))

# create a color image
aligned_im = np.dstack([ar, ag, b])

# Pyramid alignment
pa_dy_r, pa_dx_r = pyramid_align(r, b, "ncc", margin=2, verbose=True)
print(f"Pyramid displacement vector for r: {pa_dy_r, pa_dx_r}")
pa_r = np.roll(r, shift=(pa_dy_r, pa_dx_r), axis=(0, 1))

pa_dy_g, pa_dx_g = pyramid_align(g, b, "ncc", margin=2, verbose=True)
print(f"Pyramid displacement vector for g: {pa_dy_g, pa_dx_g}")
pa_g = np.roll(g, shift=(pa_dy_g, pa_dx_g), axis=(0, 1))

pyramid_aligned_im = np.dstack([pa_r, pa_g, b])

# Pyramid alignment with cropped images
pac_dy_r, pac_dx_r = pyramid_align(cropped_r, cropped_b, "ncc", verbose=True)
print(f"Pyramid + cropped displacement vector for r: {pac_dy_r, pac_dx_r}")
pa_r = np.roll(cropped_r, shift=(pac_dy_r, pac_dx_r), axis=(0, 1))

pac_dy_g, pac_dx_g = pyramid_align(cropped_g, cropped_b, "ncc", verbose=True)
print(f"Pyramid + cropped displacement vector for g: {pac_dy_g, pac_dx_g}")
pa_g = np.roll(cropped_g, shift=(pac_dy_g, pac_dx_g), axis=(0, 1))

pyramid_aligned_cropped_im = np.dstack([pa_r, pa_g, cropped_b])

# Display the images (original vs. aligned)
fig, ax = plt.subplots(2, 2, figsize=(16, 12))
ax[0, 0].imshow(orig_im)
ax[0, 0].set_title("Original")

ax[0, 1].imshow(aligned_im)
ax[0, 1].set_title(
    f"Single-Scale Aligned | r {int(dy_r), int(dx_r)}, g {int(dy_g), int(dx_g)}"
)

ax[1, 0].imshow(aligned_im)
ax[1, 0].set_title(
    f"Pyramid Aligned | r {int(pa_dy_r), int(pa_dx_r)}, g {int(pa_dy_g), int(pa_dx_g)}"
)

ax[1, 1].imshow(pyramid_aligned_cropped_im)
ax[1, 1].set_title(
    f"Pyramid + Cropped Aligned | r {int(pac_dy_r), int(pac_dx_r)}, g {int(pac_dy_g), int(pac_dx_g)}"
)

plt.tight_layout()
plt.show()

# Save the image
fname = f"{OUTPUT_DIR}{input_file}_out.jpg"
im_out_uint8 = (pyramid_aligned_cropped_im * 255.0).astype(np.uint8)
skio.imsave(fname, im_out_uint8)
print(f"Saved image to {fname}")


def align_image_pipeline(input_file_path, output_path, display=False):
    """Run the full image alignment pipeline:
    - Read the image from the input file path
    - Separate the colored glass plates
    - Crop the white and black edges
    - Align R and G plates to the B plate using the image pyramid implementation
    - Shift all three plates and stack the shifted plates
    - Trim the stacked image to only keep actually overlapping regions and exclude
        any pixels that wrapped around after shifting the R and G plates with np.roll
    - Save the aligned image
    """
    im = skio.imread(input_file_path)
    im = sk.img_as_float(im)

    # Compute the height of each part (just 1/3 of total)
    height = np.floor(im.shape[0] / 3.0).astype(np.uint64)

    # Separate color channels
    # NOTE: each glass plate image in the data folder is in BGR order
    b = im[:height]
    g = im[height : 2 * height]
    r = im[2 * height : 3 * height]

    orig_im = np.dstack([r, g, b])

    im_out_uint8 = (orig_im * 255.0).astype(np.uint8)
    orig_output_path = str(output_path).split("_out")[0] + "_original.jpg"
    skio.imsave(orig_output_path, im_out_uint8)
    print(f"Saved stacked original image to {orig_output_path}")

    crop_white_r, crop_white_g, crop_white_b = crop_rgb(r, g, b, color_val=1.0)
    crop_black_r, crop_black_g, crop_black_b = crop_rgb(
        crop_white_r, crop_white_g, crop_white_b, color_val=0.1
    )

    cropped_r, cropped_g, cropped_b = crop_black_r, crop_black_g, crop_black_b

    dy_r, dx_r = pyramid_align(cropped_r, cropped_b, "ncc")
    print(f"Displacement vector for r: {dy_r, dx_r}")
    shifted_r = np.roll(cropped_r, shift=(dy_r, dx_r), axis=(0, 1))

    dy_g, dx_g = pyramid_align(cropped_g, cropped_b, "ncc")
    print(f"Displacement vector for g: {dy_g, dx_g}")
    shifted_g = np.roll(cropped_g, shift=(dy_g, dx_g), axis=(0, 1))

    # Align shifted plates with base plate (B)
    pyramid_aligned_cropped_im = np.dstack([shifted_r, shifted_g, cropped_b])

    # Trim to only keep parts of the stacked image that corresponds to
    # where the R, G, and B plates actually overlap after shifting
    trim_top = abs(max(dy_r, dy_g, 0))
    trim_bottom = abs(min(dy_r, dy_g, 0))
    trim_left = abs(max(dx_r, dx_g, 0))
    trim_right = abs(min(dx_r, dx_g, 0))
    final_color_im = pyramid_aligned_cropped_im

    if trim_top > 0:
        final_color_im = final_color_im[trim_top:, :]
    if trim_bottom > 0:
        final_color_im = final_color_im[:-trim_bottom, :]
    if trim_left > 0:
        final_color_im = final_color_im[:, trim_left:]
    if trim_right > 0:
        final_color_im = final_color_im[:, :-trim_right]

    if display:
        # Display the original image and the aligned image
        fig, ax = plt.subplots(1, 2, figsize=(24, 12))
        ax[0].imshow(orig_im)
        ax[0].set_title("Original")

        ax[1].imshow(final_color_im)
        ax[1].set_title("Pyramid Aligned")
        plt.show()

    im_out_uint8 = (final_color_im * 255.0).astype(np.uint8)
    skio.imsave(output_path, im_out_uint8)
    print(f"Saved aligned image to {output_path}")


def compare_alignment_algorithms(input_file_path, output_path_base, display=True):
    im = skio.imread(input_file_path)
    im = sk.img_as_float(im)

    # Compute the height of each part (just 1/3 of total)
    height = np.floor(im.shape[0] / 3.0).astype(np.uint64)

    # Separate color channels
    # NOTE: each glass plate image in the data folder is in BGR order
    b = im[:height]
    g = im[height : 2 * height]
    r = im[2 * height : 3 * height]

    orig_im = np.dstack([r, g, b])

    im_out_uint8 = (orig_im * 255.0).astype(np.uint8)
    orig_output_path = output_path_base +  "_original.jpg"
    skio.imsave(orig_output_path, im_out_uint8)
    print(f"Saved stacked original image to {orig_output_path}")

    # Image pyramid alignment
    print("[Image pyramid] Starting alignment...")
    ipa_start_time = time.perf_counter()

    ipa_dy_r, ipa_dx_r = pyramid_align(r, b, "ncc")
    ipa_shifted_r = np.roll(r, shift=(ipa_dy_r, ipa_dx_r), axis=(0, 1))
    ipa_red_end_time = time.perf_counter()
    print(
        f"[Image pyramid] Aligned red to blue plate in {ipa_red_end_time - ipa_start_time} seconds"
    )

    ipa_dy_g, ipa_dx_g = pyramid_align(g, b, "ncc")
    ipa_shifted_g = np.roll(g, shift=(ipa_dy_g, ipa_dx_g), axis=(0, 1))
    ipa_green_end_time = time.perf_counter()
    print(
        f"[Image pyramid] Aligned green to blue plate in {ipa_green_end_time - ipa_red_end_time} seconds"
    )

    ipa_end_time = time.perf_counter()
    image_pyramid_alignment_time = ipa_end_time - ipa_start_time

    print(
        f"[Image pyramid] Alignment took a total of {image_pyramid_alignment_time} seconds"
    )
    print(f"[Image pyramid] Displacement vector for r: {ipa_dy_r, ipa_dx_r}")
    print(f"[Image pyramid] Displacement vector for g: {ipa_dy_g, ipa_dx_g}")

    pyramid_aligned_im = np.dstack([ipa_shifted_r, ipa_shifted_g, b])

    pyramid_out_uint8 = (pyramid_aligned_im * 255.0).astype(np.uint8)
    pyramid_output_path = output_path_base + "_pyramid.jpg"
    skio.imsave(pyramid_output_path, pyramid_out_uint8)
    print(f"[Image pyramid] Saved image to {pyramid_output_path}")

    # Single-scale alignment
    print("[Single-scale] Starting alignment...")
    ssa_start_time = time.perf_counter()

    # Run single-scale alignment algo and search a radius at least as big as the displacement found by the image pyramid algo
    ssa_dy_r, ssa_dx_r = align(
        r, b, "ncc", y_radius=abs(ipa_dy_r), x_radius=abs(ipa_dx_r), verbose=False
    )
    ssa_shifted_r = np.roll(r, shift=(ssa_dy_r, ssa_dx_r), axis=(0, 1))
    ssa_red_end_time = time.perf_counter()
    print(
        f"[Single-scale] Aligned red to blue plate in {ssa_red_end_time - ssa_start_time} seconds"
    )

    ssa_dy_g, ssa_dx_g = align(
        g, b, "ncc", y_radius=abs(ipa_dy_g), x_radius=abs(ipa_dx_g), verbose=False
    )
    ssa_shifted_g = np.roll(g, shift=(ssa_dy_g, ssa_dx_g), axis=(0, 1))
    ssa_green_endtime = time.perf_counter()
    print(
        f"[Single-scale] Aligned green to blue plate in {ssa_green_endtime - ssa_red_end_time} seconds"
    )

    ssa_end_time = time.perf_counter()
    single_scale_alignment_time = ssa_end_time - ssa_start_time

    print(
        f"[Single-scale] Alignment took a total of {single_scale_alignment_time} seconds"
    )
    print(f"[Single-scale] Displacement vector for r: {ssa_dy_r, ssa_dx_r}")
    print(f"[Single-scale] Displacement vector for g: {ssa_dy_g, ssa_dx_g}")

    single_scale_alignment_im = np.dstack([ssa_shifted_r, ssa_shifted_g, b])
    single_scale_out_uint8 = (single_scale_alignment_im * 255.0).astype(np.uint8)
    single_scale_output_path = output_path_base +  "_single_scale.jpg"
    skio.imsave(single_scale_output_path, single_scale_out_uint8)
    print(f"[Single-scale] Saved image to {single_scale_output_path}")

    if display:
        # Display the original image and the aligned image
        fig, ax = plt.subplots(1, 3, figsize=(24, 12))
        ax[0].imshow(orig_im)
        ax[0].set_title("Original")

        ax[1].imshow(single_scale_alignment_im)
        ax[1].set_title("Single-Scale")

        ax[2].imshow(pyramid_aligned_im)
        ax[2].set_title("Image Pyramid")
        plt.show()


if __name__ == "__main__":
    # Folder with the unzipped .tif or .jpg digitized glass plate images
    input_dir = Path("data")

    # Folder to save the aligned images to
    output_dir = Path("out/comparisons")

    # Iterate through the glass plates in input_dir, align each, and save the outputs
    for file_path in input_dir.iterdir():
        if file_path.is_file() and file_path.suffix in {".tif", ".jpg"}:
            base_name = file_path.stem
            output_path = str(output_dir / base_name)
            print(f"Processing {file_path}")
            # align_image_pipeline(file_path, output_path)
            compare_alignment_algorithms(file_path, output_path_base=output_path)
