# CS180 (CS280A): Project 1

import numpy as np
import skimage as sk
import skimage.io as skio
import matplotlib.pyplot as plt

DATA_DIR = "data/"
OUTPUT_DIR = "out/"

# name of the input file
imname = DATA_DIR + "cathedral.jpg"

# read in the image
im = skio.imread(imname)
plt.imshow(im)

print(im.dtype)  # dtype: unit8

# convert to double (might want to do this later on to save memory)
im = sk.img_as_float(im)

print(im.dtype)  # dtype: float64

# compute the height of each part (just 1/3 of total)
# NOTE: need to use uint64 because uint8 is [0, 255] and any value
height = np.floor(im.shape[0] / 3.0).astype(np.uint64)

# separate color channels
# NOTE: each glass plate image in the data folder is in BGR order
b = im[:height]
g = im[height : 2 * height]
r = im[2 * height : 3 * height]

orig_im = np.dstack([r, g, b])


class ShapeMismatchError(Exception):
    """Raised when two matrices have incompatible shapes"""


class UnrecognizedArgumentError(Exception):
    """Raised when an unrecognized argument is passed to a function"""


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
def align(img, base_img, metric="l2", verbose=True):
    """Align img to the base_img.

    Displacements (dy, dx) are calculated based on the assumption that the origin (0, 0)
    refers to the top left corner of the matrix/image.

    Positive dy shifts downward, positive dx shifts rightward.

    Args:
        img: np.ndarray
        base_img: the base image to align img to
        metric: "l2" or "ncc" - whether to score alignment
            by minimizing L2 distance or maximizing NCC
        verbose

    Returns:
        best_alignment: the image shifted with np.roll
        best_dy: number of pixels to displace in the y-direction
            to achieve the best alignment metric between img and base_img
        best_dx: number of pixels to displace in the x-direction
            to achieve the best alignment metric between img and base_img

    Raises:
        UnrecognizedArgumentError: If metric is not L2 distance or Normalized Cross Correlation
    """
    if metric != "l2" and metric != "ncc":
        raise UnrecognizedArgumentError("metric should be either l2 or ncc")

    best_dy, best_dx = 0, 0
    best_metric = np.inf if metric == "l2" else -np.inf

    # Score only the center of the base image and the candidate displacements.
    # np.roll wraps pixels to the opposite edge, so the glass-plate borders
    # can dominate the scoring metrics if not excluded.
    h, w = base_img.shape
    trim_edges = max(int(np.round(0.05 * min(h, w))), 15)
    trimmed_base = base_img[trim_edges:-trim_edges, trim_edges:-trim_edges]

    for dy in np.arange(-15, 16):
        for dx in np.arange(-15, 16):
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
        print(
            f"Displacement vector (dy, dx): {best_dy, best_dx}"
        )
    best_alignment = np.roll(img, shift=(best_dy, best_dx), axis=(0, 1))
    return best_alignment, best_dy, best_dx


# align
ar, dy_r, dx_r = align(r, b, "l2")
ag, dy_g, dx_g = align(g, b, "l2")

# create a color image
aligned_im = np.dstack([ar, ag, b])

# Only keep the areas of each color plate that overlap after displacing
trim_y = max(abs(dy_r), abs(dy_g))
trim_x = max(abs(dx_r), abs(dx_g))
trimmed_aligned_im = aligned_im[trim_y : -trim_y, trim_x : -trim_x, :]

# display the images (original vs. aligned)
fig, ax = plt.subplots(1, 2)
ax[0].imshow(orig_im)
ax[0].set_title("Original")

ax[1].imshow(aligned_im)
ax[1].set_title("Aligned")
plt.show()

# save the image
# fname = OUTPUT_DIR + "output.jpg"
# im_out_uint8 = (im_out * 255.0).astype(np.uint8)
# print(im_out_uint8)
# skio.imsave(fname, im_out_uint8)
