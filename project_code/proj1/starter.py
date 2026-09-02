# CS180 (CS280A): Project 1

import numpy as np
import skimage as sk
import skimage.io as skio
import matplotlib.pyplot as plt

DATA_DIR = "data/"
OUTPUT_DIR = "output/"

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


class ShapeMismatchError(Exception):
    """Raised when two matrices have incompatible shapes"""


def l2_distance(mat1: np.ndarray, mat2: np.ndarray):
    """
    Returns the L2 norm of the difference between 2 matrices (Euclidean distance)

    || mat1 - mat2 || = sqrt(sum(mat1 - mat2)) where the difference is taken element-wise
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


# arr1 = np.array([[1, 0, 0], [0, 1, 0]])
# arr2 = np.array([[0, 1, 2], [3, 4, 5]])

# print(l2_distance(arr1, arr2))  # 7.0
# print(normalized_cross_correlation(arr1, arr2))


# align the images
# functions that might be useful for aligning the images include:
# np.roll, np.sum, sk.transform.rescale (for multiscale)
def align(img, target_img):
    """
    Align img to the target_img
    """
    best_dy, best_dx = 0, 0
    best_dist = np.inf

    for dy in np.arange(-15, 15):
        for dx in np.arange(-15, 15):
            rolled = np.roll(img, shift=(dy, dx), axis=(0, 1))
            dist = l2_distance(rolled, target_img)
            if dist < best_dist:
                best_dist = dist
                best_dy, best_dx = dy, dx

    print(f"Smallest distance found {best_dist} with displacement vector {best_dy, best_dx} (dy, dx)")
    best_alignment = np.roll(img, shift=(best_dy, best_dx), axis=(0, 1))
    return best_alignment


print(l2_distance(g, b))
print(l2_distance(r, b))

orig_out = np.dstack([r, g, b])

# align
ag = align(g, b)
ar = align(r, b)
# create a color image
im_out = np.dstack([ar, ag, b])

# save the image
fname = OUTPUT_DIR + "out_fname.jpg"
skio.imsave(fname, im_out)

# display the images (original vs. aligned)
fig, ax = plt.subplots(1, 2)
ax[0].imshow(orig_out)
ax[0].set_title("Original")

ax[1].imshow(im_out)
ax[1].set_title("Aligned")
plt.show()
