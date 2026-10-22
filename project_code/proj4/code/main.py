import numpy as np
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
                color=colors[len(im1_pts)],
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
                color=colors[len(im2_pts)],
                marker="o",
                markersize=6,
            )
            fig.canvas.draw()
            im2_pts.append([event.xdata, event.ydata])
            next_axs = (next_axs + 1) % 2
        else:
            print(f"Please select a point in image {next_axs + 1} next")

        if len(im1_pts) == num_correspondences & len(im2_pts) == num_correspondences:
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
    # A = [[x, y, 1, 0, 0, 0, 0, 0 ],
    #      [0, 0, 0, x, y, 1, 0, 0],
    #      [0, 0, 0, 0, 0, 0, x, y],
    #      ... ]
    #
    N = im1_pts.shape[0]
    A = np.zeros((3 * N, 8))
    b = np.zeros((3 * N,))

    for i in range(N):
        x1, y1 = im1_pts[i]
        x2, y2 = im2_pts[i]
        A[3 * i, :3] = [x1, y1, 1]
        A[3 * i + 1, 3:6] = [x1, y1, 1]
        A[3 * i + 2, 6:] = [x1, y1]

        b[i : i + 3,] = [x2, y2, 1]

    print(f"A {A}")
    print(f"b {b}")

    h, _, _, _ = np.linalg.lstsq(A, b)

    # Convert h from a column vector into a matrix
    H = np.ones((3, 3))
    for i in range(8):
        row, col = i // 3, i % 3
        H[row, col] = h[i]

    return H


def main():
    print("Hello world!")
    # im1_pts = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    # im2_pts = np.array([[-1, -2], [-3, -4], [-5, -6], [-7, -8]])
    # computeH(im1_pts, im2_pts)

    img1 = img_to_np(DATA_DIR / "engineering_1.jpg")
    img2 = img_to_np(DATA_DIR / "engineering_2.jpg")

    im1_pts, im2_pts = get_correspondences(img1, img2)

    H = computeH(im1_pts, im2_pts)
    print(f"Recovered homography matrix: {H}")

if __name__ == "__main__":
    main()
