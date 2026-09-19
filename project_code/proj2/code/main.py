import numpy as np
import cv2 as cv
import scipy
import skimage as sk
import matplotlib.pyplot as plt
from pathlib import Path


def make_difference_and_box_filters():
    """Quick helper function to quickly update Dx, Dy, and box_filter in a singel place"""
    Dx = np.array([1, 0, -1])
    Dx = np.expand_dims(Dx, axis=0)  # Reshape row vector into (d, 1)
    Dy = np.array([[1], [0], [-1]])
    box_filter = np.ones((9, 9)) / 81

    return Dx, Dy, box_filter


def make_box_filter(size=9):
    """Make a box_filter of a given size"""
    return np.ones((size, size)) / (size**2)


def make_2d_gaussian_kernel(size=3, sigma=None):
    """Make a 2D Gaussian kernel"""
    # Size needs to be odd and positive
    if sigma:
        gaussian_filter = cv.getGaussianKernel(size, sigma)
    else:
        # OpenCV will automatically calculate a sigma based on the size if sigma is non-positive
        gaussian_filter = cv.getGaussianKernel(size, sigma=0)

    return gaussian_filter @ gaussian_filter.T


def read_img_as_float(input_file_path):
    img = sk.io.imread(input_file_path)
    img = sk.img_as_float(img)

    # Convert 4-channeled RGBA images into RGB images
    if img.shape[-1] > 3:
        img = sk.color.rgba2rgb(img)

    return img


def make_sharpening_filter(alpha=0.25, size=3, sigma=None):
    """Make a 2D Unsharp mask filter (1 + alpha) * e - alpha * g"""
    gaussian = make_2d_gaussian_kernel(size, sigma)
    unit_impulse = np.zeros((size, size))
    unit_impulse[size // 2, size // 2] = 1

    unsharp_mask_filter = (1 + alpha) * unit_impulse - alpha * gaussian
    return unsharp_mask_filter


def crop_into_square(matrix):
    h, w = matrix.shape
    min_dim = min(h, w)
    start_y = (h - min_dim) // 2
    start_x = (w - min_dim) // 2
    return matrix[start_y : start_y + min_dim, start_x : start_x + min_dim]


def convolve_2d(matrix, filter, quad_for_loop=False):
    """Part 1.1: Convolutions from Scratch!"""
    # D_out = np.floor((D_in - K + 2P) / S) + 1
    # P = ((D_out - 1) * S - D_in + K) / 2

    h, w = matrix.shape

    if len(filter.shape) < 2:
        # Reshape row vector into (d, 1) matrix
        filter = np.expand_dims(filter, axis=0)
    fh, fw = filter.shape

    # Pad the input image using same-padding (output shape = input shape), filling with constant value = 0
    y_pad = (fh - 1) // 2
    x_pad = (fw - 1) // 2
    padded = np.pad(
        matrix, ((y_pad, y_pad), (x_pad, x_pad)), mode="constant", constant_values=0
    )
    # pad_h, pad_w = padded.shape
    # print(padded)

    flip_filter = np.flip(filter)

    out = np.zeros((h, w))

    if quad_for_loop:
        # Quadruple for-loop implementation
        for oy in range(h):
            for ox in range(w):
                for fy in range(fh):
                    for fx in range(fw):
                        out[oy, ox] += flip_filter[fy, fx] * padded[oy + fy, ox + fx]
    else:
        # Double for-loop implementation
        for oy in range(h):
            for ox in range(w):
                out[oy, ox] = np.sum(
                    flip_filter * padded[oy : oy + fh, ox : ox + fw], axis=None
                )

    return out


def finite_difference_operator(input_file_path="data/cameraman.png"):
    """Part 1.2: Finite Difference Operator"""
    Dx, Dy, _ = make_difference_and_box_filters()

    img = read_img_as_float(input_file_path)
    img_grayscale = sk.color.rgb2gray(img)
    img_square = crop_into_square(img_grayscale)

    img_out_Dx = scipy.signal.convolve2d(img_square, Dx, mode="same", fillvalue=0)
    img_out_Dy = scipy.signal.convolve2d(img_square, Dy, mode="same", fillvalue=0)

    # Edge strength = ||∇f|| = sqrt((df/dx)^2 + (df/dy)^2)
    # Values range from [0, sqrt(2)]
    img_es = np.sqrt((img_out_Dx**2) + (img_out_Dy) ** 2)

    # Binarize edges: suppress noise and only keep edges above a certain threshold
    # for th in np.arange(0.1, 0.31, 0.01):
    #     threshold = th
    #     above_threshold_mask = img_es >= threshold  # bool mask
    #     img_be = img_es * above_threshold_mask

    #     fig, ax = plt.subplots(1, 2, figsize=(12, 12))
    #     ax[0].imshow(img_square, cmap="gray", vmin=0, vmax=1)
    #     ax[0].set_title("Original (grayscale)")

    #     ax[1].imshow(img_be, cmap="gray", vmin=0, vmax=1)
    #     ax[1].set_title(f"Binarized edges with threshold {th:.3f}")

    #     plt.show()

    # Best threshold (visually) = 0.26
    threshold = 0.26
    above_threshold_mask = img_es >= threshold  # bool mask
    img_be = img_es * above_threshold_mask

    fig, ax = plt.subplots(1, 2, figsize=(12, 12))
    ax[0].imshow(img_square, cmap="gray", vmin=0, vmax=1)
    ax[0].set_title("Original (grayscale)")

    ax[1].imshow(img_be, cmap="gray", vmin=0, vmax=1)
    ax[1].set_title(f"Binarized edges with threshold {threshold:.3f}")

    path = Path(input_file_path)
    stem = path.stem

    plt.savefig(f"out/{stem}_fd_binarized_edges.jpg")
    plt.show()


def derivative_of_gaussian_filter(input_file_path="data/cameraman.png"):
    """Derivative of Gaussian (DoG) Filter"""
    gaussian_filter = make_2d_gaussian_kernel(3)
    Dx, Dy, _ = make_difference_and_box_filters()

    img = read_img_as_float(input_file_path)  # in rgba format
    img_grayscale = sk.color.rgb2gray(img)
    img_square = crop_into_square(img_grayscale)

    # 2-step DoG: apply Gaussian, then convolve with finite difference filters
    img_2step_blurred = scipy.signal.convolve2d(
        img_square, gaussian_filter, mode="full", fillvalue=0
    )
    img_2step_out_Dx = scipy.signal.convolve2d(
        img_2step_blurred, Dx, mode="same", fillvalue=0
    )
    img_2step_out_Dy = scipy.signal.convolve2d(
        img_2step_blurred, Dy, mode="same", fillvalue=0
    )

    img_2step_es = np.sqrt((img_2step_out_Dx**2) + (img_2step_out_Dy) ** 2)

    # Binarize edges: suppress noise and only keep edges above a certain threshold
    # for th in np.arange(0.05, 0.18, 0.01):
    #     threshold = th
    #     above_threshold_mask = img_es >= threshold  # bool mask
    #     img_be = img_es * above_threshold_mask

    #     fig, ax = plt.subplots(1, 2, figsize=(12, 12))
    #     ax[0].imshow(img_grayscale, cmap="gray", vmin=0, vmax=1)
    #     ax[0].set_title("Original (grayscale)")

    #     ax[1].imshow(img_be, cmap="gray", vmin=0, vmax=1)
    #     ax[1].set_title(f"Binarized edges with threshold {th:.3f}")

    #     plt.show()

    # Best threshold (visually) = 0.13
    threshold = 0.13
    threshold_mask = img_2step_es >= threshold  # bool mask
    img_2step_be = img_2step_es * threshold_mask

    fig, ax = plt.subplots(1, 2, figsize=(12, 12))
    ax[0].imshow(img_grayscale, cmap="gray", vmin=0, vmax=1)
    ax[0].set_title("Original (grayscale)")

    ax[1].imshow(img_2step_be, cmap="gray", vmin=0, vmax=1)
    ax[1].set_title(
        f"Gaussian blur then Dx, Dy: Binarized edges with threshold {threshold:.3f}"
    )

    path = Path(input_file_path)
    stem = path.stem
    plt.savefig(f"out/{stem}_2step_dog.jpg")
    plt.show()

    # 1-step DoG: convolve Gaussian finite difference filters, then convolve the result ONCE with the image
    dog_filter_Dx = scipy.signal.convolve2d(
        gaussian_filter, Dx, mode="full", fillvalue=0
    )
    dog_filter_Dy = scipy.signal.convolve2d(
        gaussian_filter, Dy, mode="full", fillvalue=0
    )
    img_1step_out_Dx = scipy.signal.convolve2d(
        img_square, dog_filter_Dx, mode="same", fillvalue=0
    )
    img_1step_out_Dy = scipy.signal.convolve2d(
        img_square, dog_filter_Dy, mode="same", fillvalue=0
    )

    img_1step_es = np.sqrt((img_1step_out_Dx**2) + (img_1step_out_Dy) ** 2)
    threshold_mask_1step = img_1step_es >= threshold
    img_1step_be = img_1step_es * threshold_mask_1step

    fig, ax = plt.subplots(1, 3, figsize=(12, 12))
    ax[0].imshow(img_square, cmap="gray", vmin=0, vmax=1)
    ax[0].set_title("Original (grayscale)")

    ax[1].imshow(img_2step_be, cmap="gray", vmin=0, vmax=1)
    ax[1].set_title(
        f"Gaussian blur then Dx, Dy: Binarized edges with threshold {threshold:.3f}"
    )

    ax[2].imshow(img_1step_be, cmap="gray", vmin=0, vmax=1)
    ax[2].set_title(f"DoG: Binarized edges with threshold {threshold:.3f}")

    path = Path(input_file_path)
    stem = path.stem

    plt.savefig(f"out/{stem}_dog_comparison.jpg")
    plt.show()


def sharpen(input_img=None, input_file_path="data/taj.jpg", alpha=0.25):
    """
    Part 2.1: Image "Sharpening"
    """
    sharpening_filter = make_sharpening_filter(alpha=alpha, size=3)

    if input_img is not None:
        img = input_img
    else:
        img = read_img_as_float(input_file_path)

    img_r = img[:, :, 0]
    img_g = img[:, :, 1]
    img_b = img[:, :, 2]

    sharp_r = scipy.signal.convolve2d(
        img_r, sharpening_filter, mode="same", fillvalue=0
    )
    sharp_g = scipy.signal.convolve2d(
        img_g, sharpening_filter, mode="same", fillvalue=0
    )
    sharp_b = scipy.signal.convolve2d(
        img_b, sharpening_filter, mode="same", fillvalue=0
    )

    sharp_img = np.dstack((sharp_r, sharp_g, sharp_b))
    sharp_img = np.clip(sharp_img, 0.0, 1.0)

    fig, ax = plt.subplots(1, 2, figsize=(8, 4), layout="constrained")
    ax[0].imshow(img, vmin=0, vmax=1)
    ax[0].set_title("Original")

    ax[1].imshow(sharp_img, vmin=0, vmax=1)
    ax[1].set_title(f"Sharpened with alpha {alpha}")

    fig.suptitle('Part 2.1: Image "Sharpening"')

    path = Path(input_file_path)
    stem = path.stem

    plt.savefig(f"out/{stem}_compare_sharpened.jpg")
    plt.show()

    return sharp_img


def sharpen_then_blur_then_sharpen(input_file_path="data/taj.jpg", alpha=0.25):
    """
    Part 2.1: Image "Sharpening" continued
    """
    original_img = read_img_as_float(input_file_path)
    sharp_img1 = sharpen(input_file_path=input_file_path)

    gaussian = make_2d_gaussian_kernel(size=3)
    sharp_img1_r = sharp_img1[:, :, 0]
    sharp_img1_g = sharp_img1[:, :, 1]
    sharp_img1_b = sharp_img1[:, :, 2]

    blur_img_r = scipy.signal.convolve2d(
        sharp_img1_r, gaussian, mode="same", fillvalue=0
    )
    blur_img_g = scipy.signal.convolve2d(
        sharp_img1_g, gaussian, mode="same", fillvalue=0
    )
    blur_img_b = scipy.signal.convolve2d(
        sharp_img1_b, gaussian, mode="same", fillvalue=0
    )

    blur_img = np.dstack((blur_img_r, blur_img_g, blur_img_b))

    sharp_img2 = sharpen(input_img=blur_img, alpha=0.25)

    fig, ax = plt.subplots(2, 2, figsize=(8, 8), layout="constrained")
    ax[0, 0].imshow(original_img, vmin=0, vmax=1)
    ax[0, 0].set_title("Original")

    ax[0, 1].imshow(sharp_img1, vmin=0, vmax=1)
    ax[0, 1].set_title(f"Sharpened with alpha {alpha}")

    ax[1, 0].imshow(blur_img, vmin=0, vmax=1)
    ax[1, 0].set_title("Sharpened then blurred")

    ax[1, 1].imshow(sharp_img2, vmin=0, vmax=1)
    ax[1, 1].set_title("Sharpened then blurred then re-sharpened")

    fig.suptitle("Part 2.1: Sharpen + Blur + Sharpen")

    path = Path(input_file_path)
    stem = path.stem
    plt.savefig(f"out/{stem}_compare_sharpen_blur_sharpen.jpg")
    plt.show()


def main():
    Dx, Dy, box_filter = make_difference_and_box_filters()

    img = read_img_as_float("data/deenasun_square.jpg")

    img_grayscale = sk.color.rgb2gray(img)  # dtype: float64, shape: (w, h)

    out_Dx = convolve_2d(img_grayscale, Dx)
    out_Dy = convolve_2d(img_grayscale, Dy)
    out_box = convolve_2d(img_grayscale, box_filter)

    fig, ax = plt.subplots(2, 2, figsize=(12, 12))
    ax[0, 0].imshow(img_grayscale, cmap="gray", vmin=0, vmax=1)
    ax[0, 0].set_title("Original (grayscale)")

    ax[0, 1].imshow(out_Dx, cmap="viridis", vmin=0, vmax=1)
    ax[0, 1].set_title("After convolving with Dx")

    ax[1, 0].imshow(out_Dy, cmap="viridis", vmin=0, vmax=1)
    ax[1, 0].set_title("After convolving with Dy")

    ax[1, 1].imshow(out_box, cmap="gray", vmin=0, vmax=1)
    ax[1, 1].set_title("After convolving with box filter")

    plt.show()

    # Compare with scipy.signal.convolve2d
    scipy_out_Dx = scipy.signal.convolve2d(
        img_grayscale, np.expand_dims(Dx, axis=0), mode="same", fillvalue=0
    )
    scipy_out_Dy = scipy.signal.convolve2d(img_grayscale, Dy, mode="same", fillvalue=0)
    scipy_out_box = scipy.signal.convolve2d(
        img_grayscale, box_filter, mode="same", fillvalue=0
    )

    assert np.allclose(out_Dx, scipy_out_Dx, atol=1e-8), (
        "Convolution with Dx does not match scipy.signal.convolve2d"
    )
    assert np.allclose(out_Dy, scipy_out_Dy, atol=1e-8), (
        "Convolution with Dy does not match scipy.signal.convolve2d"
    )
    assert np.allclose(out_box, scipy_out_box, atol=1e-8), (
        "Convolution with box filter does not match scipy.signal.convolve2d"
    )
