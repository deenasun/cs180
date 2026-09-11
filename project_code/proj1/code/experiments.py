import json
import time
import numpy as np
import skimage as sk
import skimage.io as skio
import matplotlib.pyplot as plt
from pathlib import Path

from main import (
    align,
    crop_rgb,
    pyramid_align,
    edge_detection_align,
    DATA_DIR,
    OUTPUT_DIR,
)


def plot_alignment_barchart():
    with open("alignment_results.json", "r", encoding="utf-8") as file:
        alignment_results = json.load(file)

    image_names = set()
    barchart_data = {"single_scale": [], "pyramid": []}

    for ar in alignment_results:
        input_file_name = ar["input_file_name"].split(".")[0]
        single_scale_time = ar["single_scale_total_time_elapsed"]
        pyramid_time = ar["image_pyramid_total_time_elapsed"]

        barchart_data["single_scale"].append(single_scale_time)
        barchart_data["pyramid"].append(pyramid_time)
        image_names.add(input_file_name)

    fig, ax = plt.subplots(1, 1)
    ax.grouped_bar(
        barchart_data,
        tick_labels=image_names,
        group_spacing=1,
        orientation="horizontal",
    )

    ax.set_xlabel("Alignment algo time (sec)")
    ax.set_title("Single-scale vs. Image Pyramid Alignment Time")
    ax.legend(loc="upper right")
    plt.grid(axis="x", alpha=0.5)

    plt.tight_layout()
    plt.show()


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
    orig_output_path = output_path_base + "_original.jpg"
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
    single_scale_output_path = output_path_base + "_single_scale.jpg"
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


def compare_metrics(input_file_path, output_path_base, display=True):
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
    orig_output_path = output_path_base + "_original.jpg"
    skio.imsave(orig_output_path, im_out_uint8)
    print(f"Saved stacked original image to {orig_output_path}")

    # L2 norm
    print("[L2 Norm] Starting alignment...")
    l2_start_time = time.perf_counter()

    l2_dy_r, l2_dx_r = pyramid_align(r, b, "l2")
    l2_shifted_r = np.roll(r, shift=(l2_dy_r, l2_dx_r), axis=(0, 1))

    l2_dy_g, l2_dx_g = pyramid_align(g, b, "l2")
    l2_shifted_g = np.roll(g, shift=(l2_dy_g, l2_dx_g), axis=(0, 1))

    l2_end_time = time.perf_counter()

    print(f"[L2 Norm] Displacement vector for r: {l2_dy_r, l2_dx_r}")
    print(f"[L2 Norm] Displacement vector for g: {l2_dy_g, l2_dx_g}")
    print(f"[L2 Norm] Alignment took a total of {l2_end_time - l2_start_time} seconds")

    l2_aligned_im = np.dstack([l2_shifted_r, l2_shifted_g, b])

    l2_out_uint8 = (l2_aligned_im * 255.0).astype(np.uint8)
    l2_output_path = output_path_base + "_l2.jpg"
    skio.imsave(l2_output_path, l2_out_uint8)
    print(f"[L2 Norm] Saved image to {l2_output_path}")

    # NCC
    print("[NCC] Starting alignment...")
    ncc_start_time = time.perf_counter()

    ncc_dy_r, ncc_dx_r = pyramid_align(r, b, "ncc")
    ncc_shifted_r = np.roll(r, shift=(ncc_dy_r, ncc_dx_r), axis=(0, 1))

    ncc_dy_g, ncc_dx_g = pyramid_align(g, b, "ncc")
    ncc_shifted_g = np.roll(g, shift=(ncc_dy_g, ncc_dx_g), axis=(0, 1))

    ncc_end_time = time.perf_counter()

    print(f"[NCC] Displacement vector for r: {ncc_dy_r, ncc_dx_r}")
    print(f"[NCC] Displacement vector for g: {ncc_dy_g, ncc_dx_g}")
    print(f"[NCC] Alignment took a total of {ncc_end_time - ncc_start_time} seconds")

    ncc_aligned_im = np.dstack([ncc_shifted_r, ncc_shifted_g, b])

    ncc_out_uint8 = (ncc_aligned_im * 255.0).astype(np.uint8)
    ncc_output_path = output_path_base + "_ncc.jpg"
    skio.imsave(ncc_output_path, ncc_out_uint8)
    print(f"[NCC] Saved image to {ncc_output_path}")

    if display:
        # Display the original image and the aligned image
        fig, ax = plt.subplots(1, 3, figsize=(24, 12))
        ax[0].imshow(orig_im)
        ax[0].set_title("Original")

        ax[1].imshow(l2_aligned_im)
        ax[1].set_title("L2 Norm")

        ax[2].imshow(ncc_aligned_im)
        ax[2].set_title("NCC")
        plt.show()


def process_results_gallery(input_file_path, output_path_base, display=True):

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
    orig_output_path = str(output_path_base) + "_original.jpg"
    skio.imsave(orig_output_path, im_out_uint8)
    print(f"Saved stacked original image to {orig_output_path}")

    crop_white_r, crop_white_g, crop_white_b = crop_rgb(r, g, b, color_val=1.0)
    crop_black_r, crop_black_g, crop_black_b = crop_rgb(
        crop_white_r, crop_white_g, crop_white_b, color_val=0.1
    )

    cropped_r, cropped_g, cropped_b = crop_black_r, crop_black_g, crop_black_b

    # Image Pyramid + L2 norm
    l2_dy_r, l2_dx_r = pyramid_align(cropped_r, cropped_b, "l2")
    l2_shifted_r = np.roll(cropped_r, shift=(l2_dy_r, l2_dx_r), axis=(0, 1))

    l2_dy_g, l2_dx_g = pyramid_align(cropped_g, cropped_b, "l2")
    l2_shifted_g = np.roll(cropped_g, shift=(l2_dy_g, l2_dx_g), axis=(0, 1))

    print(f"[Image Pyramid + L2 Norm] Displacement vector for r: {l2_dy_r, l2_dx_r}")
    print(f"[Image Pyramid + L2 Norm] Displacement vector for g: {l2_dy_g, l2_dx_g}")

    l2_aligned_im = np.dstack([l2_shifted_r, l2_shifted_g, cropped_b])

    # Trim to only keep parts of the stacked image that corresponds to
    # where the R, G, and B plates actually overlap after shifting
    l2_trim_top = abs(max(l2_dy_r, l2_dy_g, 0))
    l2_trim_bottom = abs(min(l2_dy_r, l2_dy_g, 0))
    l2_trim_left = abs(max(l2_dx_r, l2_dx_g, 0))
    l2_trim_right = abs(min(l2_dx_r, l2_dx_g, 0))

    if l2_trim_top > 0:
        l2_aligned_im = l2_aligned_im[l2_trim_top:, :]
    if l2_trim_bottom > 0:
        l2_aligned_im = l2_aligned_im[:-l2_trim_bottom, :]
    if l2_trim_left > 0:
        l2_aligned_im = l2_aligned_im[:, l2_trim_left:]
    if l2_trim_right > 0:
        l2_aligned_im = l2_aligned_im[:, :-l2_trim_right]

    l2_out_uint8 = (l2_aligned_im * 255.0).astype(np.uint8)
    l2_output_path = output_path_base + "_l2_out.jpg"
    skio.imsave(l2_output_path, l2_out_uint8)
    print(f"[Image Pyramid + L2 Norm] Saved image to {l2_output_path}")

    # Image Pyramid + NCC
    print("[Image Pyramid + NCC] Starting alignment...")

    ncc_dy_r, ncc_dx_r = pyramid_align(cropped_r, cropped_b, "ncc")
    ncc_shifted_r = np.roll(cropped_r, shift=(ncc_dy_r, ncc_dx_r), axis=(0, 1))

    ncc_dy_g, ncc_dx_g = pyramid_align(cropped_g, cropped_b, "ncc")
    ncc_shifted_g = np.roll(cropped_g, shift=(ncc_dy_g, ncc_dx_g), axis=(0, 1))

    print(f"[Image Pyramid + NCC] Displacement vector for r: {ncc_dy_r, ncc_dx_r}")
    print(f"[Image Pyramid + NCC] Displacement vector for g: {ncc_dy_g, ncc_dx_g}")

    ncc_aligned_im = np.dstack([ncc_shifted_r, ncc_shifted_g, cropped_b])

    # Trim to only keep parts of the stacked image that corresponds to
    # where the R, G, and B plates actually overlap after shifting
    ncc_trim_top = abs(max(ncc_dy_r, ncc_dy_g, 0))
    ncc_trim_bottom = abs(min(ncc_dy_r, ncc_dy_g, 0))
    ncc_trim_left = abs(max(ncc_dx_r, ncc_dx_g, 0))
    ncc_trim_right = abs(min(ncc_dx_r, ncc_dx_g, 0))

    if ncc_trim_top > 0:
        ncc_aligned_im = ncc_aligned_im[ncc_trim_top:, :]
    if ncc_trim_bottom > 0:
        ncc_aligned_im = ncc_aligned_im[:-ncc_trim_bottom, :]
    if ncc_trim_left > 0:
        ncc_aligned_im = ncc_aligned_im[:, ncc_trim_left:]
    if ncc_trim_right > 0:
        ncc_aligned_im = ncc_aligned_im[:, :-ncc_trim_right]

    ncc_out_uint8 = (ncc_aligned_im * 255.0).astype(np.uint8)
    ncc_output_path = output_path_base + "_ncc_out.jpg"
    skio.imsave(ncc_output_path, ncc_out_uint8)
    print(f"[Image Pyramid + NCC] Saved image to {ncc_output_path}")

    # Image Pyramid + Canny Edge Detector
    if display:
        # Display detected edges
        fig, ax = plt.subplots(1, 3, figsize=(24, 12))
        ax[0].imshow(cropped_r, cmap="gray", vmin=0, vmax=1)
        ax[0].set_title("Red plate")

        ax[1].imshow(cropped_g, cmap="gray", vmin=0, vmax=1)
        ax[1].set_title("Green plate")

        blue_im = ax[2].imshow(
            cropped_b, cmap="gray", vmin=0, vmax=1
        )  # Colorbar needs an image returned by imshow
        ax[2].set_title("Blue plate")

        # Colorbar for pixel intensities
        plt.colorbar(
            blue_im,
            ax=ax,
            label="Pixel intensity",
            orientation="horizontal",
            fraction=0.05,
            pad=0.05,
        )
        plt.show()

    r_edges = sk.feature.canny(cropped_r).astype(
        np.float64
    )  # Cast from bool into floats
    g_edges = sk.feature.canny(cropped_g).astype(np.float64)
    b_edges = sk.feature.canny(cropped_b).astype(np.float64)

    if display:
        # Display detected edges
        fig, ax = plt.subplots(1, 3, figsize=(24, 12))
        ax[0].imshow(r_edges, cmap="gray")
        ax[0].set_title("Red edges")

        ax[1].imshow(g_edges, cmap="gray")
        ax[1].set_title("Green edges")

        ax[2].imshow(b_edges, cmap="gray")
        ax[2].set_title("Blue edges")

        plt.show()

    canny_dy_r, canny_dx_r = pyramid_align(r_edges, b_edges, "ncc")
    print(
        f"[Image Pyramid + Canny Edge Detector + NCC] Displacement vector for r: {canny_dy_r, canny_dx_r}"
    )
    canny_shifted_r = np.roll(cropped_r, shift=(canny_dy_r, canny_dx_r), axis=(0, 1))

    canny_dy_g, canny_dx_g = pyramid_align(g_edges, b_edges, "ncc")
    print(
        f"[Image Pyramid + Canny Edge Detector + NCC] Displacement vector for g: {canny_dy_g, canny_dx_g}"
    )
    canny_shifted_g = np.roll(cropped_g, shift=(canny_dy_g, canny_dx_g), axis=(0, 1))

    # Align shifted plates with base plate (B)
    canny_im = np.dstack([canny_shifted_r, canny_shifted_g, cropped_b])

    # Trim to only keep parts of the stacked image that corresponds to
    # where the R, G, and B plates actually overlap after shifting
    canny_trim_top = abs(max(canny_dy_r, canny_dy_g, 0))
    canny_trim_bottom = abs(min(canny_dy_r, canny_dy_g, 0))
    canny_trim_left = abs(max(canny_dx_r, canny_dx_g, 0))
    canny_trim_right = abs(min(canny_dx_r, canny_dx_g, 0))

    if canny_trim_top > 0:
        canny_im = canny_im[canny_trim_top:, :]
    if canny_trim_bottom > 0:
        canny_im = canny_im[:-canny_trim_bottom, :]
    if canny_trim_left > 0:
        canny_im = canny_im[:, canny_trim_left:]
    if canny_trim_right > 0:
        canny_im = canny_im[:, :-canny_trim_right]

    canny_im_out_uint8 = (canny_im * 255.0).astype(np.uint8)
    canny_output_path = output_path_base + "_canny_out.jpg"
    skio.imsave(canny_output_path, canny_im_out_uint8)
    print(
        f"[Image Pyramid + Canny Edge Detector + NCC] Saved aligned image to {canny_output_path}"
    )

    if display:
        # Display the original image and the aligned image
        fig, ax = plt.subplots(2, 2, figsize=(24, 24))
        ax[0, 0].imshow(orig_im)
        ax[0, 0].set_title("Original")

        ax[0, 1].imshow(l2_aligned_im)
        ax[0, 1].set_title("Image Pyramid + L2")

        ax[1, 0].imshow(ncc_aligned_im)
        ax[1, 0].set_title("Image Pyramid + NCC")

        ax[1, 1].imshow(canny_im)
        ax[1, 1].set_title("Image Pyramid + Canny Edge Detector")
        plt.show()


def main():

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

    print(
        f"{input_file}{input_file_extension} has dimensions {height} x {width} (h x w)"
    )

    # separate color channels
    # NOTE: each glass plate image in the data folder is in BGR order
    b = im[:height]
    g = im[height : 2 * height]
    r = im[2 * height : 3 * height]

    # stack color channels into original image
    orig_im = np.dstack([r, g, b])

    crop_white_r, crop_white_g, crop_white_b = crop_rgb(r, g, b, color_val=1.0)
    crop_black_r, crop_black_g, crop_black_b = crop_rgb(
        crop_white_r, crop_white_g, crop_white_b, color_val=0.1
    )

    cropped_r, cropped_g, cropped_b = crop_black_r, crop_black_g, crop_black_b

    # plt.imshow(cropped_r)
    # plt.imshow(cropped_g)
    # plt.imshow(cropped_b)

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

    # Folder with the unzipped .tif or .jpg digitized glass plate images
    input_dir = Path("data")

    # Folder to save the aligned images to
    output_dir = Path("out")

    # Iterate through the glass plates in input_dir, align each, and save the outputs
    for file_path in input_dir.iterdir():
        if file_path.is_file() and file_path.suffix in {".tif", ".jpg"}:
            base_name = file_path.stem
            output_path_base = str(output_dir / base_name)
            print(f"Processing {file_path}")
            # compare_alignment_algorithms(file_path, output_path_base=output_path_base)
            # compare_metrics(file_path, output_path_base=output_path)
            process_results_gallery(file_path, output_path_base, display=True)


if __name__ == "__main__":
    main()
