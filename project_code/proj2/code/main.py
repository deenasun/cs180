import numpy as np
import scipy
import skimage as sk
import matplotlib.pyplot as plt

# D_out = np.floor((D_in - K + 2P) / S) + 1
# P = ((D_out - 1) * S - D_in + K) / 2
Dx = np.array([1, 0, -1])
Dy = np.array([[1], [0], [-1]])
box_filter = np.ones((9, 9)) / 81


def convolve_2d(matrix, filter, quad_for_loop=False):
    """Part 1.1: Convolutions from Scratch!"""
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


def make_box_filter(size=9):
    return np.ones((size, size)) / (size**2)


def finite_difference_cameraman():
    """Part 1.2: Finite Difference Operator"""
    cameraman_img = sk.io.imread("data/cameraman.png")  # in rgba format
    cameraman_rgb = sk.color.rgba2rgb(cameraman_img)
    cameraman_grayscale = sk.color.rgb2gray(cameraman_rgb)

    fig, ax = plt.subplots(2, 2, figsize=(12, 12))
    ax[0, 0].imshow(cameraman_grayscale, cmap="gray", vmin=0, vmax=1)
    ax[0, 0].set_title("Original (grayscale)")

    cameraman_out_Dx = convolve_2d(cameraman_grayscale, Dx)
    cameraman_out_Dy = convolve_2d(cameraman_grayscale, Dy)

    # edge strength = ||∇f|| = sqrt((df/dx)^2 + (df/dy)^2)
    cameraman_es = np.sqrt((cameraman_out_Dx**2) + (cameraman_out_Dy) ** 2)

    # ax[0, 1].imshow(out_Dx, cmap="viridis", vmin=0, vmax=1)
    # ax[0, 1].set_title("After convolving with Dx")

    # ax[1, 0].imshow(out_Dy, cmap="viridis", vmin=0, vmax=1)
    # ax[1, 0].set_title("After convolving with Dy")

    # ax[1, 1].imshow(out_box, cmap="gray", vmin=0, vmax=1)
    # ax[1, 1].set_title("After convolving with box filter")

    plt.show()


def main():
    Dx = np.array([1, 0, -1])
    Dy = np.array([[1], [0], [-1]])
    box_filter = make_box_filter(size=9)

    img = sk.io.imread("data/deenasun_square.jpg")

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
