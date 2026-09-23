import numpy as np
import cv2 as cv
import scipy
import skimage as sk
import matplotlib.pyplot as plt
from pathlib import Path
from align_image_code import align_images

DATA_DIR = "data"
OUTPUT_DIR = "out"


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
        gaussian_filter = cv.getGaussianKernel(size=3, sigma=0)

    return gaussian_filter @ gaussian_filter.T


def ndarray_to_uint8_img(arr):
    """Helper function to convert a NumPy ndarray into uint8 for saving"""
    is_float = np.issubdtype(arr.dtype, np.floating)
    if is_float:
        arr_uint8 = (arr * 255.0).astype(np.uint8)
        return arr_uint8
    else:
        return arr.astype(np.uint8)


def read_img_as_float(input_file_path, grayscale=False):
    img = sk.io.imread(input_file_path)
    img = sk.img_as_float(img)

    # Convert 4-channeled RGBA images into RGB images
    if img.shape[-1] > 3:
        img = sk.color.rgba2rgb(img)

    if grayscale:
        img = sk.color.rgb2gray(img)

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
    h, w = matrix.shape

    if len(filter.shape) < 2:
        # Reshape row vector into (d, 1) matrix
        filter = np.expand_dims(filter, axis=0)
    fh, fw = filter.shape

    # D_out = np.floor((D_in - K + 2P) / S) + 1
    # P = ((D_out - 1) * S - D_in + K) / 2
    # Pad input image using same-padding s.t. output shape = input shape
    # Fill with constant value = 0
    y_pad = (fh - 1) // 2
    x_pad = (fw - 1) // 2
    padded = np.pad(
        matrix, ((y_pad, y_pad), (x_pad, x_pad)), mode="constant", constant_values=0
    )

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

    # Compare with scipy.signal.convolve2d
    scipy_out = scipy.signal.convolve2d(matrix, filter, mode="same", fillvalue=0)
    assert np.allclose(out, scipy_out, atol=1e-8), (
        "Convolution does not match scipy.signal.convolve2d"
    )

    return out


def finite_difference_operator(input_file_path=f"{DATA_DIR}/cameraman.png"):
    """Part 1.2: Finite Difference Operator"""
    input_stem = Path(input_file_path).stem
    Dx, Dy, _ = make_difference_and_box_filters()

    img = read_img_as_float(input_file_path)
    img_grayscale = sk.color.rgb2gray(img)
    img_square = crop_into_square(img_grayscale)

    img_out_Dx = scipy.signal.convolve2d(img_square, Dx, mode="same", fillvalue=0)

    plt.imshow(img_out_Dx, cmap="gray")
    plt.title("Convolution with Dx")
    plt.savefig(f"{OUTPUT_DIR}/{input_stem}_conv_dx.jpg", bbox_inches="tight")

    img_out_Dy = scipy.signal.convolve2d(img_square, Dy, mode="same", fillvalue=0)
    plt.imshow(img_out_Dy, cmap="gray")
    plt.title("Convolution with Dy")
    plt.savefig(f"{OUTPUT_DIR}/{input_stem}_conv_dy.jpg", bbox_inches="tight")

    # Edge strength = ||∇f|| = sqrt((df/dx)^2 + (df/dy)^2)
    # Values range from [0, sqrt(2)]
    img_es = np.sqrt((img_out_Dx**2) + (img_out_Dy) ** 2)

    # Try different thresholds to select the best one for binarizing edges
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

    # Binarize edges: suppress noise and only keep edges above a certain threshold
    # Best threshold (visually) = 0.26
    threshold = 0.26
    above_threshold_mask = img_es >= threshold  # bool mask
    # img_be = img_es * above_threshold_mask
    img_be = (above_threshold_mask).astype(float)

    plt.imshow(img_be, cmap="gray")
    plt.title(f"Edge strength (binarized) w/ threshold {threshold:.3f}")
    plt.savefig(
        f"{OUTPUT_DIR}/{input_stem}_binarized_edge_magnitude.jpg", bbox_inches="tight"
    )

    fig, ax = plt.subplots(2, 2, figsize=(12, 12))
    ax[0, 0].imshow(img_square, cmap="gray", vmin=0, vmax=1)
    ax[0, 0].set_title("Original (grayscale)")

    ax[0, 1].imshow(img_be, cmap="gray", vmin=0, vmax=1)
    ax[0, 1].set_title(f"Edge strength (binarized) w/ threshold {threshold:.3f}")

    ax[1, 1].imshow(img_out_Dx, cmap="gray")
    ax[1, 1].set_title("Convolution with Dx")

    ax[1, 0].imshow(img_out_Dy, cmap="gray")
    ax[1, 0].set_title("Convolution with Dy")

    plt.savefig(
        f"{OUTPUT_DIR}/{input_stem}_finite_difference_operators.jpg",
        bbox_inches="tight",
    )
    plt.show()


def derivative_of_gaussian_filter(input_file_path=f"{DATA_DIR}/cameraman.png"):
    """Part 1.3: Derivative of Gaussian (DoG) Filter"""
    input_stem = Path(input_file_path).stem
    guassian_size = 9
    gaussian_filter = make_2d_gaussian_kernel(guassian_size)
    Dx, Dy, _ = make_difference_and_box_filters()

    img = read_img_as_float(input_file_path)  # in rgba format
    img_grayscale = sk.color.rgb2gray(img)
    img_square = crop_into_square(img_grayscale)

    # 2-step DoG: apply Gaussian, then convolve with finite difference filters
    img_2step_blurred = scipy.signal.convolve2d(
        img_square, gaussian_filter, mode="full", fillvalue=0
    )

    plt.imshow(img_2step_blurred, cmap="gray")
    plt.title("Convolve with a Gaussian filter to blur")
    plt.savefig(
        f"{OUTPUT_DIR}/{input_stem}_2step_dog_gaussian.jpg", bbox_inches="tight"
    )

    img_2step_out_Dx = scipy.signal.convolve2d(
        img_2step_blurred, Dx, mode="same", fillvalue=0
    )
    plt.imshow(img_2step_out_Dx, cmap="gray")
    plt.title("Convolve blurred image with Dx")
    plt.savefig(f"{OUTPUT_DIR}/{input_stem}_2step_dog_dx.jpg", bbox_inches="tight")

    img_2step_out_Dy = scipy.signal.convolve2d(
        img_2step_blurred, Dy, mode="same", fillvalue=0
    )
    plt.imshow(img_2step_out_Dy, cmap="gray")
    plt.title("Convolve blurred image with Dy")
    plt.savefig(f"{OUTPUT_DIR}/{input_stem}_2step_dog_dy.jpg", bbox_inches="tight")

    img_2step_es = np.sqrt((img_2step_out_Dx**2) + (img_2step_out_Dy) ** 2)

    # Try different thresholds to select the best one for binarizing edges
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

    # Binarize edges: suppress noise and only keep edges above a certain threshold
    # Best threshold (visually) = 0.13
    threshold = 0.13
    threshold_mask = img_2step_es >= threshold  # bool mask
    img_2step_be = (threshold_mask).astype(float)

    plt.imshow(img_2step_be, cmap="gray", vmin=0, vmax=1)
    plt.title(f"Blur then Dx, Dy (binarized edges, threshold: {threshold:.3f})")

    plt.savefig(f"{OUTPUT_DIR}/{input_stem}_2step_dog.jpg", bbox_inches="tight")
    plt.show()

    # 1-step DoG: convolve Gaussian finite difference filters, then convolve the result ONCE with the image
    dog_filter_Dx = scipy.signal.convolve2d(
        gaussian_filter, Dx, mode="full", fillvalue=0
    )
    dog_filter_Dy = scipy.signal.convolve2d(
        gaussian_filter, Dy, mode="full", fillvalue=0
    )

    # Visualize the DoG filters
    fig, ax = plt.subplots(1, 2, figsize=(12, 12))
    # ax[0].imshow(dog_filter_Dx, cmap="gray", vmin=0, vmax=1)
    ax[0].imshow(dog_filter_Dx)
    ax[0].set_title(
        f"Derivative of a {guassian_size}x{guassian_size} Gaussian (Gaussian * Dx)"
    )

    # ax[1].imshow(dog_filter_Dy, cmap="gray", vmin=0, vmax=1)
    ax[1].imshow(dog_filter_Dy)

    ax[1].set_title(
        f"Derivative of a {guassian_size}x{guassian_size} Gaussian (Gaussian * Dy)"
    )

    plt.savefig(
        f"{OUTPUT_DIR}/{input_stem}_gaussian_derivatives.jpg", bbox_inches="tight"
    )
    plt.show()

    img_1step_out_Dx = scipy.signal.convolve2d(
        img_square, dog_filter_Dx, mode="same", fillvalue=0
    )
    plt.imshow(img_1step_out_Dx, cmap="gray", vmin=0, vmax=1)
    plt.title("DoG in a single conv (Dx)")
    plt.savefig(f"{OUTPUT_DIR}/{input_stem}_1step_dog_dx.jpg", bbox_inches="tight")

    img_1step_out_Dy = scipy.signal.convolve2d(
        img_square, dog_filter_Dy, mode="same", fillvalue=0
    )
    plt.imshow(img_1step_out_Dy, cmap="gray", vmin=0, vmax=1)
    plt.title("DoG in a single conv (Dy)")
    plt.savefig(f"{OUTPUT_DIR}/{input_stem}_1step_dog_dy.jpg", bbox_inches="tight")

    img_1step_es = np.sqrt((img_1step_out_Dx**2) + (img_1step_out_Dy) ** 2)
    threshold_mask_1step = img_1step_es >= threshold
    img_1step_be = (threshold_mask_1step).astype(float)

    plt.imshow(img_1step_be, cmap="gray", vmin=0, vmax=1)
    plt.title(f"DoG in a single conv (binarized edges, threshold: {threshold:.3f})")
    plt.savefig(f"{OUTPUT_DIR}/{input_stem}_1step_dog.jpg", bbox_inches="tight")

    fig, ax = plt.subplots(1, 3, figsize=(8, 12))
    ax[0].imshow(img_square, cmap="gray", vmin=0, vmax=1)
    ax[0].set_title("Original (grayscale)")

    ax[1].imshow(img_2step_be, cmap="gray", vmin=0, vmax=1)
    ax[1].set_title("2-conv DoG")

    ax[2].imshow(img_1step_be, cmap="gray", vmin=0, vmax=1)
    ax[2].set_title("1-conv DoG")

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/{input_stem}_dog_comparison.jpg", bbox_inches="tight")
    plt.show()


def sharpen(input_img=None, input_file_path=f"{DATA_DIR}/taj.jpg", alpha=1.0):
    """
    Part 2.1: Image "Sharpening"
    """
    sharpening_filter = make_sharpening_filter(alpha=alpha, size=9)

    if input_img is not None:
        img = input_img
        stem = "img"
    else:
        img = read_img_as_float(input_file_path)
        stem = Path(input_file_path).stem

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

    plt.imshow(sharp_img)
    plt.title(f"Sharpened with alpha {alpha}")
    plt.savefig(f"{OUTPUT_DIR}/{stem}_sharpen_{alpha}.jpg", bbox_inches="tight")

    fig, ax = plt.subplots(1, 2, figsize=(8, 4), layout="constrained")
    ax[0].imshow(img, vmin=0, vmax=1)
    ax[0].set_title("Original")

    ax[1].imshow(sharp_img, vmin=0, vmax=1)
    ax[1].set_title(f"Sharpened with alpha {alpha}")

    fig.suptitle('Part 2.1: Image "Sharpening"')

    plt.savefig(f"{OUTPUT_DIR}/{stem}_compare_sharpened.jpg", bbox_inches="tight")
    plt.show()

    return sharp_img


def sharpen_alpha_experiments(input_file_path=f"{DATA_DIR}/taj.jpg"):
    """Sharpen images with different alphas, display, and save results"""
    img = read_img_as_float(input_file_path)
    input_stem = Path(input_file_path).stem

    alphas = [0.01, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
    sharpened_images = {}
    for alpha in alphas:
        res = sharpen(img, alpha=alpha)
        sharpened_images[alpha] = res

    fig, ax = plt.subplots(4, 2, figsize=(8, 20), layout="constrained")
    ax[0, 0].imshow(img, vmin=0, vmax=1)
    ax[0, 0].set_title("Original")

    ax[0, 1].imshow(sharpened_images[0.01], vmin=0, vmax=1)
    ax[0, 1].set_title(f"Sharpened with alpha {0.01}")

    ax[1, 0].imshow(sharpened_images[0.1], vmin=0, vmax=1)
    ax[1, 0].set_title(f"Sharpened with alpha {0.1}")

    ax[1, 1].imshow(sharpened_images[0.25], vmin=0, vmax=1)
    ax[1, 1].set_title(f"Sharpened with alpha {0.25}")

    ax[2, 0].imshow(sharpened_images[0.5], vmin=0, vmax=1)
    ax[2, 0].set_title(f"Sharpened with alpha {0.5}")

    ax[2, 1].imshow(sharpened_images[1.0], vmin=0, vmax=1)
    ax[2, 1].set_title(f"Sharpened with alpha {1.0}")

    ax[3, 0].imshow(sharpened_images[2.0], vmin=0, vmax=1)
    ax[3, 0].set_title(f"Sharpened with alpha {2.0}")

    ax[3, 1].imshow(sharpened_images[5.0], vmin=0, vmax=1)
    ax[3, 1].set_title(f"Sharpened with alpha {5.0}")

    fig.suptitle('Part 2.1: Image "Sharpening"')

    plt.savefig(f"{OUTPUT_DIR}/{input_stem}_sharpen_alphas.jpg", bbox_inches="tight")
    plt.show()


def sharpen_then_blur_then_sharpen(input_file_path=f"{DATA_DIR}/taj.jpg", alpha=1.0):
    """
    Part 2.1: Image "Sharpening" continued
    """
    original_img = read_img_as_float(input_file_path)
    sharp_img1 = sharpen(input_file_path=input_file_path)
    input_stem = Path(input_file_path).stem

    gaussian = make_2d_gaussian_kernel(size=9)
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

    sharp_img2 = sharpen(input_img=blur_img, alpha=alpha)

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
    plt.savefig(
        f"{OUTPUT_DIR}/{input_stem}_sharpen_blur_sharpen.jpg", bbox_inches="tight"
    )
    plt.show()


def hybrid_image(img1, img2, hf_sigma, lf_sigma, show_ft=False):
    """
    Part 2.2: Hybrid Images

    The cut-off frequency where the Gaussian's frequency response falls to 1/2 its original amplitude:
        f_c = (sqrt(2 * ln(2)) / (2 * pi * sigma) ≈ 0.187 / sigma

    So doubling the sigma halves the cutoff frequency.
    """

    def high_pass_filter(img, sigma):
        # Rule of thumb for Gaussian filters: set filter half-width to about 3 sigma
        kernel_size = 2 * int(np.ceil(3 * sigma)) + 1
        gaussian = make_2d_gaussian_kernel(size=kernel_size, sigma=sigma)
        if len(img.shape) == 2:
            gaussian_conv = scipy.signal.convolve2d(
                img, gaussian, mode="same", fillvalue=0
            )
            high_pass_out = img - gaussian_conv
        elif len(img.shape) == 3:
            high_pass_outs = []
            for c in range(img.shape[-1]):
                channel = img[:, :, c]
                gaussian_conv = scipy.signal.convolve2d(
                    channel, gaussian, mode="same", fillvalue=0
                )
                hp_channel_out = channel - gaussian_conv
                high_pass_outs.append(hp_channel_out)
            high_pass_out = np.dstack(high_pass_outs)
        else:
            print(
                f"Input image should have 2 or 3 dimensions, but input had shape {img.shape}"
            )
            return None

        return high_pass_out

    def low_pass_filter(img, sigma):
        # Rule of thumb for Gaussian filters: set filter half-width to about 3 sigma
        kernel_size = 2 * int(np.ceil(3 * sigma)) + 1
        gaussian = make_2d_gaussian_kernel(size=kernel_size, sigma=sigma)
        if len(img.shape) == 2:
            low_pass_out = scipy.signal.convolve2d(
                img, gaussian, mode="same", fillvalue=0
            )
        elif len(img.shape) == 3:
            low_pass_outs = []
            for c in range(img.shape[-1]):
                channel = img[:, :, c]
                lp_channel_out = scipy.signal.convolve2d(
                    channel, gaussian, mode="same", fillvalue=0
                )
                low_pass_outs.append(lp_channel_out)
            low_pass_out = np.dstack(low_pass_outs)
        else:
            print(
                f"Input image should have 2 or 3 dimensions, but input had shape {img.shape}"
            )
            return None

        return low_pass_out

    high_freq_img = high_pass_filter(img1, hf_sigma)
    low_freq_img = low_pass_filter(img2, lf_sigma)

    hybrid = low_freq_img + high_freq_img
    hybrid = np.clip(hybrid, 0.0, 1.0)

    # Display images and their log magnitude Fourier Transforms
    # np.fft.fft2 computes the 2D Fourier transform by converting pixel brightness into spatial-frequency components
    # np.fft.fftshift moves the zero-frequency to the center;
    #   low frequencies are near the center and high frequences are on the periphery
    if show_ft:
        fig, ax = plt.subplots(nrows=5, ncols=2, figsize=(10, 20), layout="constrained")

        img1_gray = sk.color.rgb2gray(img1)
        img1_ft = np.log(np.abs(np.fft.fftshift(np.fft.fft2(img1_gray))))

        img2_gray = sk.color.rgb2gray(img2)
        img2_ft = np.log(np.abs(np.fft.fftshift(np.fft.fft2(img2_gray))))

        hf_gray = sk.color.rgb2gray(high_freq_img)
        hf_ft = np.log(np.abs(np.fft.fftshift(np.fft.fft2(hf_gray))))

        lf_gray = sk.color.rgb2gray(low_freq_img)
        lf_ft = np.log(np.abs(np.fft.fftshift(np.fft.fft2(lf_gray))))

        hybrid_gray = sk.color.rgb2gray(hybrid)
        hybrid_ft = np.log(np.abs(np.fft.fftshift(np.fft.fft2(hybrid_gray))))

        # Compute min/max across all Fourier Transform plots so each imshow has consistent vmin/vmax
        ft_min = min(
            [img1_ft.min(), img2_ft.min(), hf_ft.min(), lf_ft.min(), hybrid_ft.min()]
        )
        ft_max = min(
            [img1_ft.max(), img2_ft.max(), hf_ft.max(), lf_ft.max(), hybrid_ft.max()]
        )

        ax[0, 0].imshow(img1)
        ax[0, 0].set_title("Image 1")
        ax[0, 1].imshow(img1_ft, cmap="gray", vmin=ft_min, vmax=ft_max)
        ax[0, 1].set_title("Image 1 (FT log magnitude)")

        ax[1, 0].imshow(img2)
        ax[1, 0].set_title("Image 2")
        ax[1, 1].imshow(img2_ft, cmap="gray", vmin=ft_min, vmax=ft_max)
        ax[1, 1].set_title("Image 2 (FT log magnitude)")

        ax[2, 0].imshow(high_freq_img)
        ax[2, 0].set_title(f"Image 1 w/ high-pass filter σ={hf_sigma}")
        ax[2, 1].imshow(hf_ft, cmap="gray", vmin=ft_min, vmax=ft_max)
        ax[2, 1].set_title("Image 1 w/ high-pass filter (FT log magnitude)")

        ax[3, 0].imshow(low_freq_img)
        ax[3, 0].set_title("Image 2 w/ low-pass filter σ={lf_sigma}")
        ax[3, 1].imshow(lf_ft, cmap="gray", vmin=ft_min, vmax=ft_max)
        ax[3, 1].set_title("Image 2 w/ low-pass filter (FT log magnitude)")

        ax[4, 0].imshow(hybrid)
        ax[4, 0].set_title("Hybrid image")
        ax[4, 1].imshow(hybrid_ft, cmap="gray", vmin=ft_min, vmax=ft_max)
        ax[4, 1].set_title("Hybrid image (FT log magnitude)")

        plt.show()

    return hybrid


def load_align_hybrid(
    img1_file_path=f"{DATA_DIR}/DerekPicture.jpg",
    img2_file_path=f"{DATA_DIR}/nutmeg.jpg",
):
    """
    Part 2.2: Hybrid Images

    This function implements the full pipeline for part 2.2: loading 2 images, aligning them, then hybridizing them.
    """
    # high sf
    # img1 = plt.imread("{DATA_DIR}/DerekPicture.jpg") / 255.0
    # # low sf
    # img2 = plt.imread("{DATA_DIR}/nutmeg.jpg") / 255.0

    # # high sf
    # img1 = plt.imread("{DATA_DIR}/cheetah.jpg") / 255.0
    # # low sf
    # img2 = plt.imread("{DATA_DIR}/honey_badger.jpg") / 255.0

    # # high sf
    # img1 = read_img_as_float("{DATA_DIR}/burger.jpg")
    # # low sf
    # img2 = read_img_as_float("{DATA_DIR}/saturn.jpg")

    # First load images
    img1 = read_img_as_float(img1_file_path)
    img2 = read_img_as_float(img2_file_path)

    # Align images
    img1_aligned, img2_aligned = align_images(img1, img2)

    plt.imshow(img1_aligned)
    plt.show()
    plt.imshow(img2_aligned)
    plt.show()

    # Trying a matrix of different sigma values for the high-pass and low-pass filters
    # hf_candidates = [2, 2.5, 3, 3.5, 4]
    # lf_candidates = [1, 2, 3, 4, 5]

    # for i1, hf_s1 in enumerate(hf_candidates):
    #     for i2, lf_s2 in enumerate(lf_candidates):
    #         print(f"Processing hf sigma1 {hf_s1}, lf sigma2 {lf_s2}")
    #         hybrid = hybrid_image(img1_aligned, img2_aligned, hf_s1, lf_s2)
    #         # idx = i1 * 7 + i2
    #         # axs[idx].imshow(hybrid)
    #         # axs[idx].set_title(f"hf {hf_s1}, lf {lf_s2}")
    #         # axs[idx].axis("off")

    #         plt.imshow(hybrid)
    #         plt.title(f"hf {hf_s1}, lf {lf_s2}")
    #         plt.show()

    hf_sigma = 2.75
    lf_sigma = 3
    hybrid = hybrid_image(img1_aligned, img2_aligned, hf_sigma, lf_sigma, show_ft=True)
    plt.imshow(hybrid)
    plt.show()


def gaussian_stack(
    input_img=None, input_file_path=f"{DATA_DIR}/apple.jpg", display=False
):
    """
    Part 2.3: Gaussian and Laplacian Stacks
    """
    if input_img is not None:
        img = input_img
    else:
        img = read_img_as_float(input_file_path)

    h, w = img.shape[:2]
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]

    # Rule of thumb for Gaussians: set filter half-width to about 3 sigma
    # Set max kernel size to ~ 1/2 width
    max_kernel_size = min(h, w) // 2
    max_sigma = (max_kernel_size) // 6

    sigma = 1
    stack = [img]

    # Implement Gaussian stack by applying bigger blurs (bigger sigma + kernel size)
    while sigma <= max_sigma and len(stack) < 8:
        print(f"Level {len(stack)}: applying gaussian with sigma {sigma}")
        gaussian_kernel = make_2d_gaussian_kernel(sigma=sigma)
        conv_r = scipy.signal.convolve2d(r, gaussian_kernel, mode="same", fillvalue=0)
        conv_g = scipy.signal.convolve2d(g, gaussian_kernel, mode="same", fillvalue=0)
        conv_b = scipy.signal.convolve2d(b, gaussian_kernel, mode="same", fillvalue=0)

        conv_stacked = np.dstack([conv_r, conv_g, conv_b])
        stack.append(conv_stacked)
        sigma *= 2

    if display:
        n_rows = (len(stack) + 1) // 2
        fig, ax = plt.subplots(nrows=n_rows, ncols=2, figsize=(6, 10))

        ax_flat = ax.flatten()

        for idx, s in enumerate(stack):
            ax_flat[idx].imshow(s)
            ax_flat[idx].set_title(f"Level {idx}")

        # Hide empty subplots
        for ax in fig.axes:
            if not ax.has_data():
                fig.delaxes(ax)

        plt.show()

    return np.array(stack)


def laplacian_stack(
    input_img=None, input_file_path="{DATA_DIR}/apple.jpg", display=False
):
    """
    Part 2.3: Gaussian and Laplacian Stacks
    """
    if input_img is not None:
        img = input_img
    else:
        img = read_img_as_float(input_file_path)

    # level 0 = highest freq, level[-1] = lowest freq (most blurred)
    gaussian_levels = gaussian_stack(img)
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

    if display:
        n_rows = (len(stack) + 1) // 2
        fig, ax = plt.subplots(nrows=n_rows, ncols=2, figsize=(6, 10))

        ax_flat = ax.flatten()

        for idx, s in enumerate(stack):
            # Laplacian levels can have negative values
            # For clearer displays, re-map values s.t. the middle value is 0.5 (gray)
            half_range = np.max(np.abs(s))
            if half_range > 0:
                remapped_s = 0.5 + s / (2 * half_range)
            else:
                remapped_s = np.full(s.shape, fill_value=0.5)
            ax_flat[idx].imshow(remapped_s)

            ax_flat[idx].set_title(f"Level {idx}")

        # Hide empty subplots
        for ax in fig.axes:
            if not ax.has_data():
                fig.delaxes(ax)

        plt.show()

    return np.array(stack)


def multiresolution_blend(
    img1_file_path="{DATA_DIR}/apple.jpg", img2_file_path="{DATA_DIR}/orange.jpg"
):
    """Part 2.4: Multiresolution Blending (a.k.a. the oraple!)"""
    img1 = read_img_as_float(img1_file_path)
    img2 = read_img_as_float(img2_file_path)

    h, w = img1.shape[:2]

    # Mask for a vertical spline:
    #   - 1's on the left where we want img1 to be visible
    #   - 0's on the right where we want img2 to be visible
    vertical_spline_mask = np.zeros_like(img1)
    vertical_spline_mask[:, : w // 2] = 1

    # Mask for a horizonal spline:
    #   - 1's on the top where we want img1 to be visible
    #   - 0's on the bottom where we want img2 to be visible
    horizonal_spline_mask = np.zeros_like(img1)
    horizonal_spline_mask[: h // 2, :] = 1

    laplacian1 = laplacian_stack(input_img=img1, display=True)
    laplacian2 = laplacian_stack(input_img=img2, display=True)
    gaussian_weights = gaussian_stack(input_img=vertical_spline_mask, display=True)

    blend_out = np.zeros_like(img1)
    for lap1, lap2, gw in zip(laplacian1, laplacian2, gaussian_weights):
        blend = gw * lap1 + (1 - gw) * lap2
        blend_out += blend

    blend_out = np.clip(blend_out, 0, 1.0)

    fig, ax = plt.subplots(1, 3, figsize=(10, 6))

    img1_path = Path(img1_file_path)
    ax[0].imshow(img1)
    ax[0].set_title(f"{img1_path.name}")

    img2_path = Path(img2_file_path)
    ax[1].imshow(img2)
    ax[1].set_title(f"{img2_path.name}")

    ax[2].imshow(blend_out)
    ax[2].set_title("Blended")

    plt.savefig(
        f"{OUTPUT_DIR}/multiresolution_blend_{img1_path.stem}_{img2_path.stem}.jpg",
        bbox_inches="tight",
    )
    plt.show()

    return blend_out


def main():
    Dx, Dy, box_filter = make_difference_and_box_filters()

    img = read_img_as_float("{DATA_DIR}/deenasun_square.jpg")

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
    ax[1, 1].set_title("After convolving with a 9x9 box filter")

    plt.savefig("{OUTPUT_DIR}/convolution_comparisons.jpg", bbox_inches="tight")
    plt.show()

    # load_align_hybrid()
    pass


if __name__ == "__main__":
    main()
