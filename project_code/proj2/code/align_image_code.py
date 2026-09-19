"""Lets the user click two corresponding points on each of two images,
then aligns the images so those two points overlap (matching center,
scale, and rotation), and crops both to a common size.
"""

import math

import numpy as np
import matplotlib.pyplot as plt
import skimage.transform as sktr


def get_points(im1: np.ndarray, im2: np.ndarray) -> tuple:
    print("Please select 2 points in each image for alignment.")
    plt.imshow(im1)
    p1, p2 = plt.ginput(2)
    plt.close()
    plt.imshow(im2)
    p3, p4 = plt.ginput(2)
    plt.close()
    return (p1, p2, p3, p4)


def recenter(im: np.ndarray, r: float, c: float) -> np.ndarray:
    R, C = im.shape[:2]
    rpad = int(np.abs(2 * r + 1 - R))
    cpad = int(np.abs(2 * c + 1 - C))
    pad_width = [
        (0 if r > (R - 1) / 2 else rpad, 0 if r < (R - 1) / 2 else rpad),
        (0 if c > (C - 1) / 2 else cpad, 0 if c < (C - 1) / 2 else cpad),
    ]
    if im.ndim == 3:
        pad_width.append((0, 0))
    return np.pad(im, pad_width, "constant")


def find_centers(p1: tuple, p2: tuple) -> tuple:
    cx = np.round(np.mean([p1[0], p2[0]]))
    cy = np.round(np.mean([p1[1], p2[1]]))
    return cx, cy


def align_image_centers(im1: np.ndarray, im2: np.ndarray, pts: tuple) -> tuple:
    p1, p2, p3, p4 = pts

    cx1, cy1 = find_centers(p1, p2)
    cx2, cy2 = find_centers(p3, p4)

    im1 = recenter(im1, cy1, cx1)
    im2 = recenter(im2, cy2, cx2)
    return im1, im2


def rescale_images(im1: np.ndarray, im2: np.ndarray, pts: tuple) -> tuple:
    p1, p2, p3, p4 = pts
    len1 = np.sqrt((p2[1] - p1[1]) ** 2 + (p2[0] - p1[0]) ** 2)
    len2 = np.sqrt((p4[1] - p3[1]) ** 2 + (p4[0] - p3[0]) ** 2)
    dscale = len2 / len1
    channel_axis = -1 if im1.ndim == 3 else None
    if dscale < 1:
        im1 = sktr.rescale(im1, dscale, channel_axis=channel_axis)
    else:
        im2 = sktr.rescale(im2, 1.0 / dscale, channel_axis=channel_axis)
    return im1, im2


def rotate_im1(im1: np.ndarray, pts: tuple) -> tuple:
    p1, p2, p3, p4 = pts
    theta1 = math.atan2(-(p2[1] - p1[1]), (p2[0] - p1[0]))
    theta2 = math.atan2(-(p4[1] - p3[1]), (p4[0] - p3[0]))
    dtheta = theta2 - theta1
    im1 = sktr.rotate(im1, dtheta * 180 / np.pi)
    return im1, dtheta


def match_img_size(im1: np.ndarray, im2: np.ndarray) -> tuple:
    # Make images the same size
    h1, w1 = im1.shape[:2]
    h2, w2 = im2.shape[:2]
    if h1 < h2:
        im2 = im2[int(np.floor((h2 - h1) / 2.0)) : -int(np.ceil((h2 - h1) / 2.0)), :]
    elif h1 > h2:
        im1 = im1[int(np.floor((h1 - h2) / 2.0)) : -int(np.ceil((h1 - h2) / 2.0)), :]
    if w1 < w2:
        im2 = im2[:, int(np.floor((w2 - w1) / 2.0)) : -int(np.ceil((w2 - w1) / 2.0))]
    elif w1 > w2:
        im1 = im1[:, int(np.floor((w1 - w2) / 2.0)) : -int(np.ceil((w1 - w2) / 2.0))]
    assert im1.shape == im2.shape
    return im1, im2


def align_images(im1: np.ndarray, im2: np.ndarray) -> tuple:
    # Collect points once
    pts = get_points(im1, im2)

    mask1 = np.ones(im1.shape[:2], dtype=float)
    mask2 = np.ones(im2.shape[:2], dtype=float)

    def align(mat1, mat2):
        mat1, mat2 = align_image_centers(mat1, mat2, pts)
        mat1, mat2 = rescale_images(mat1, mat2, pts)
        mat1, _ = rotate_im1(mat1, pts)
        mat1, mat2 = match_img_size(mat1, mat2)
        return mat1, mat2

    # Apply the alignment pipeline with the same points to the actual images and masks
    im1, im2 = align(im1, im2)

    # return im1, im2

    mask1, mask2 = align(mask1, mask2)

    # Find overlapping regions
    valid = (mask1 >= 1 - 1e-6) & (mask2 >= 1 - 1e-6)

    h, w = valid.shape
    center_x, center_y = w // 2, h // 2

    # Start with a 1-pixel rectangle and expand outwards
    # bottom, right are exclusive
    top, bottom = center_y, center_y + 1
    left, right = center_x, center_x + 1

    # Keep expanding bounds outwards while rectangle is all valid
    while True:
        expanded = False

        # Expand upwards by 1 if the next row above is all valid
        if top > 0 and valid[top - 1, left:right].all():
            top -= 1
            expanded = True

        # Expand left by 1 if the next col on the left is all valid
        if left > 0 and valid[top:bottom, left - 1].all():
            left -= 1
            expanded = True

        # Expand downwards by 1 if the next row below is all valid
        if bottom < h and valid[bottom, left:right].all():
            bottom += 1
            expanded = True

        # Expand right by 1 if the next col on the right is all valid
        if right < w and valid[top:bottom, right].all():
            right += 1
            expanded = True

        # Exit loop if we can't expand on any side
        if not expanded:
            break

    return im1[top:bottom, left:right], im2[top:bottom, left:right]


if __name__ == "__main__":
    # 1. load the image
    # 2. align the two images by calling align_images
    # Now you are ready to write your own code for creating hybrid images!

    im1 = plt.imread("data/DerekPicture.jpg") / 255.0

    im2 = plt.imread("data/nutmeg.jpg") / 255.0

    im1_aligned, im2_aligned = align_images(im1, im2)

    plt.imshow(im1_aligned)
    plt.show()

    plt.imshow(im2_aligned)
    plt.show()
