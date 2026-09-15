"use client";

import katex from "katex";
import "katex/dist/katex.min.css";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import TableOfContents from "@/components/TableOfContents";
import { getAssetPath } from "@/shared"

function Figure({
    src,
    caption,
    subcaption,
    style_width,
    style_height,
    loading
}: {
    src: string,
    caption: string,
    subcaption?: string | null
    style_width?: string | null,
    style_height?: string | null,
    loading?: "eager" | "lazy";
}) {
    // Focus on the figure if mouse hovers and stays over the image
    const [isHovering, setIsHovering] = useState(false);
    const [isFocused, setIsFocused] = useState(false);
    const hoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

    const handleMouseEnter = () => {
        setIsHovering(true);

        hoverTimer.current = setTimeout(() => {
            setIsFocused(true);
        }, 1000);
    };

    const handleMouseLeave = () => {
        setIsHovering(false);

        if (hoverTimer.current) {
            clearTimeout(hoverTimer.current);
        }
    };

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                setIsFocused(false);
            }
        };

        window.addEventListener("keydown", handleKeyDown);

        return () => {
            window.removeEventListener("keydown", handleKeyDown);

            if (hoverTimer.current) {
                clearTimeout(hoverTimer.current);
            }
        };
    }, []);

    return (
        <>
            <figure
                className={`flex w-full max-w-2xl flex-col items-center ${style_width ? "" : "mx-auto"}`}
                style={style_width ? { width: style_width } : undefined}
            >
                <div
                    className="relative cursor-zoom-in items-center"
                    onMouseEnter={handleMouseEnter}
                    onMouseLeave={handleMouseLeave}
                >
                    <Image
                        key={src}
                        src={getAssetPath(src)}
                        alt={caption}
                        height={1080}
                        width={1080}
                        loading={loading}
                        style={{
                            width: style_width ?? "auto",
                            height: style_width ? "auto" : (style_height ?? "40vh"),
                        }}
                    />
                    {isHovering && (
                        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 rounded bg-space-black/80 px-3 py-1 text-sm text-cream">
                            <span className="mr-2">Hover to zoom</span>
                            <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-cream border-t-transparent" />
                        </div>
                    )}
                </div>
                <figcaption className="mt-2 text-center text-sm text-gray-600">
                    {caption}
                </figcaption>
                {subcaption != null && (
                    <figcaption className="mt-2 text-center text-xs text-gray-600">
                        {subcaption}
                    </figcaption>
                )}
            </figure>
            {/* Smooth transition for the focus overlay */}
            <div
                className={`fixed inset-0 z-50 flex items-center justify-center bg-space-black/80 p-8
        transition-opacity duration-300 ease-out
        ${isFocused
                        ? "pointer-events-auto opacity-100"
                        : "pointer-events-none opacity-0"
                    }`}
                onClick={() => setIsFocused(false)}
            >
                <Image
                    src={getAssetPath(src)}
                    alt={caption}
                    width={2000}
                    height={2000}
                    className={`max-h-full max-w-full object-contain
            transition-transform duration-300 ease-out`}
                />
            </div>
        </>

    )
}

const galleryImages = [
    { stem: "cathedral", filename: "cathedral.jpg", noBorderCrop: "red (dy, dx): (12, 3), green (dy, dx): (5, 2)", l2: "red (dy, dx): (12, 3), green (dy, dx): (5, 2)", ncc: "red (dy, dx): (12, 3), green (dy, dx): (5, 2)", nccTime: 0.34063304198207334, canny: "red (dy, dx): (12, 3), green (dy, dx): (5, 2)", cannyTime: 0.28272237500641495 },
    { stem: "church", filename: "church.tif", noBorderCrop: "red (dy, dx): (57, -5), green (dy, dx): (-1, -5)", l2: "red (dy, dx): (58, 188), green (dy, dx): (25, 2)", ncc: "red (dy, dx): (57, -5), green (dy, dx): (24, 3)", nccTime: 19.936688084038906, canny: "red (dy, dx): (58, -4), green (dy, dx): (25, 4)", cannyTime: 19.063652332988568 },
    { stem: "emir", filename: "emir.tif", noBorderCrop: "red (dy, dx): (118, -178), green (dy, dx): (24, 8)", l2: "red (dy, dx): (104, 43), green (dy, dx): (49, 24)", ncc: "red (dy, dx): (132, -276), green (dy, dx): (49, 24)", nccTime: 19.718385333020706, canny: "red (dy, dx): (107, 40), green (dy, dx): (49, 23)", cannyTime: 18.14302591700107 },
    { stem: "harvesters", filename: "harvesters.tif", noBorderCrop: "red (dy, dx): (129, 7), green (dy, dx): (58, 10)", l2: "red (dy, dx): (124, 14), green (dy, dx): (60, 16)", ncc: "red (dy, dx): (124, 13), green (dy, dx): (60, 16)", nccTime: 20.309437874995638, canny: "red (dy, dx): (123, 9), green (dy, dx): (60, 18)", cannyTime: 18.353582709096372 },
    { stem: "icon", filename: "icon.tif", noBorderCrop: "red (dy, dx): (91, 22), green (dy, dx): (40, 16)", l2: "red (dy, dx): (90, 23), green (dy, dx): (41, 17)", ncc: "red (dy, dx): (89, 23), green (dy, dx): (40, 16)", nccTime: 20.348901292018127, canny: "red (dy, dx): (88, 22), green (dy, dx): (38, 16)", cannyTime: 20.003334500011988 },
    { stem: "ilemselga", filename: "ilemselga.tif", noBorderCrop: "red (dy, dx): (138, -7), green (dy, dx): (39, -4)", l2: "red (dy, dx): (129, 11), green (dy, dx): (39, 7)", ncc: "red (dy, dx): (130, 11), green (dy, dx): (39, 7)", nccTime: 21.66792987502413, canny: "red (dy, dx): (130, 11), green (dy, dx): (39, 7)", cannyTime: 17.579173124977387 },
    { stem: "melons", filename: "melons.tif", noBorderCrop: "red (dy, dx): (179, 8), green (dy, dx): (83, 4)", l2: "red (dy, dx): (179, 13), green (dy, dx): (82, 10)", ncc: "red (dy, dx): (178, 12), green (dy, dx): (82, 9)", nccTime: 20.561996291042306, canny: "red (dy, dx): (182, 11), green (dy, dx): (79, 9)", cannyTime: 17.75047070789151 },
    { stem: "monastery", filename: "monastery.jpg", noBorderCrop: "red (dy, dx): (3, 2), green (dy, dx): (-3, 2)", l2: "red (dy, dx): (3, 2), green (dy, dx): (-3, 2)", ncc: "red (dy, dx): (3, 2), green (dy, dx): (-3, 2)", nccTime: 0.2987282079993747, canny: "red (dy, dx): (3, 2), green (dy, dx): (-3, 2)", cannyTime: 0.28110541601199657 },
    { stem: "religous_painting", filename: "religious_painting.tif", noBorderCrop: "red (dy, dx): (69, 7), green (dy, dx): (24, 3)", l2: "red (dy, dx): (68, 7), green (dy, dx): (28, 5)", ncc: "red (dy, dx): (68, 7), green (dy, dx): (28, 5)", nccTime: 19.996679125004448, canny: "red (dy, dx): (69, 6), green (dy, dx): (29, 1)", cannyTime: 18.60476383403875 },
    { stem: "self_portrait", filename: "self_portrait.tif", noBorderCrop: "red (dy, dx): (176, -3), green (dy, dx): (77, -1)", l2: "red (dy, dx): (176, 36), green (dy, dx): (79, 28)", ncc: "red (dy, dx): (176, 36), green (dy, dx): (79, 28)", nccTime: 20.43723791697994, canny: "red (dy, dx): (175, 37), green (dy, dx): (77, 29)", cannyTime: 17.60523758304771 },
    { stem: "siren", filename: "siren.tif", noBorderCrop: "red (dy, dx): (97, -21), green (dy, dx): (48, -7)", l2: "red (dy, dx): (96, -25), green (dy, dx): (49, -6)", ncc: "red (dy, dx): (96, -25), green (dy, dx): (49, -6)", nccTime: 21.13100537500577, canny: "red (dy, dx): (96, -23), green (dy, dx): (48, -8)", cannyTime: 18.04695425007958 },
    { stem: "three_generations", filename: "three_generations.tif", noBorderCrop: "red (dy, dx): (112, 7), green (dy, dx): (52, 5)", l2: "red (dy, dx): (112, 10), green (dy, dx): (54, 12)", ncc: "red (dy, dx): (112, 10), green (dy, dx): (54, 12)", nccTime: 19.926406166981906, canny: "red (dy, dx): (111, 8), green (dy, dx): (56, 12)", cannyTime: 18.969930042047054 },
    { stem: "tobolsk", filename: "tobolsk.jpg", noBorderCrop: "red (dy, dx): (6, 3), green (dy, dx): (3, 2)", l2: "red (dy, dx): (6, 3), green (dy, dx): (3, 3)", ncc: "red (dy, dx): (6, 3), green (dy, dx): (3, 3)", nccTime: 0.31092458398779854, canny: "red (dy, dx): (6, 3), green (dy, dx): (3, 3)", cannyTime: 0.2716849159915 },
    { stem: "wharf", filename: "wharf.tif", noBorderCrop: "red (dy, dx): (83, -17), green (dy, dx): (15, -7)", l2: "red (dy, dx): (83, -17), green (dy, dx): (15, -7)", ncc: "red (dy, dx): (83, -17), green (dy, dx): (15, -7)", nccTime: 20.27525591698941, canny: "red (dy, dx): (83, -16), green (dy, dx): (15, -7)", cannyTime: 18.091458334005438 },
];

const additionalGalleryImages = [
    { stem: "laika", filename: "laika.tif", noBorderCrop: "red (dy, dx): (125, 12), green (dy, dx): (26, 5)", l2: "red (dy, dx): (115, 7), green (dy, dx): (27, 3)", ncc: "red (dy, dx): (115, 7), green (dy, dx): (27, 2)", nccTime: null, canny: "red (dy, dx): (116, 4), green (dy, dx): (28, 1)", cannyTime: 18.338085582945496 },
    { stem: "milan_duomo", filename: "milan_duomo.tif", noBorderCrop: "red (dy, dx): (111, -16), green (dy, dx): (46, -10)", l2: "red (dy, dx): (111, -15), green (dy, dx): (47, -9)", ncc: "red (dy, dx): (111, -15), green (dy, dx): (47, -9)", nccTime: null, canny: "red (dy, dx): (110, -17), green (dy, dx): (50, -6)", cannyTime: 19.01235195796471 },
    { stem: "borodino", filename: "borodino.tif", noBorderCrop: "red (dy, dx): (107, 26), green (dy, dx): (55, 13)", l2: "red (dy, dx): (109, 39), green (dy, dx): (53, 28)", ncc: "red (dy, dx): (109, 40), green (dy, dx): (54, 29)", nccTime: null, canny: "red (dy, dx): (110, 42), green (dy, dx): (51, 24)", cannyTime: 17.819363708025776 },
    { stem: "st_boris", filename: "st_boris.tif", noBorderCrop: "red (dy, dx): (118, 31), green (dy, dx): (48, 16)", l2: "red (dy, dx): (158, 62), green (dy, dx): (65, 33)", ncc: "red (dy, dx): (158, 62), green (dy, dx): (65, 33)", nccTime: null, canny: "red (dy, dx): (157, 61), green (dy, dx): (65, 35)", cannyTime: 17.78168666700367 },
];

const singleScaleTimes: Record<string, number> = {
    cathedral: 0.06523008301155642,
    church: 31.00756649998948,
    emir: 2117.252685583022,
    harvesters: 153.1230301669566,
    icon: 270.12432741594967,
    ilemselga: 122.37571508297697,
    melons: 186.6695230419864,
    monastery: 0.019149540981743485,
    religous_painting: 60.86188816698268,
    self_portrait: 74.76482054201188,
    siren: 249.66856158297742,
    three_generations: 110.15708704205463,
    tobolsk: 0.03530124999815598,
    wharf: 157.2599486670224,
};

export default function Page() {
    const contents = [
        {
            sectionLink: "context",
            text: "Background Context"
        },
        {
            sectionLink: "overview",
            text: "Overview"
        },
        {
            sectionLink: "basic_alignment",
            text: "Single-Scale Alignment"
        },
        {
            sectionLink: "single_scale_gallery",
            text: "Single-Scale Gallery"
        },
        {
            sectionLink: "image_pyramids",
            text: "Image Pyramids"
        },
        {
            sectionLink: "bells_and_whistles",
            text: "Bells and Whistles"
        },
        {
            sectionLink: "timing_comparison",
            text: "Alignment Timing Comparison"
        },
        {
            sectionLink: "final_results_gallery",
            text: "Final Results Gallery"
        },
    ]

    const l2NormEquation = String.raw`L2 = \sqrt{\sum_{i, j} (img1[i, j] - img2[i, j])^2}`

    const l2NormEquationRendered = katex.renderToString(l2NormEquation, {
        displayMode: true,
        throwOnError: false,
    });

    const NCCEquation = String.raw`NCC = \langle \frac{img1 - \mu_1}{ \lVert img1 - \mu_1 \rVert_2 },  \frac{img2 - \mu_2}{ \lVert img2 - \mu_2 \rVert_2}  \rangle`

    const NCCEquationRendered = katex.renderToString(NCCEquation, {
        displayMode: true,
        throwOnError: false,
    });

    return (
        <main className="mx-4 my-2 sm:mx-8">
            <article className="mr-[17vw] space-y-12">
                <h1 className="font-bold">Project 1: Colorizing the Prokudin-Gorskii Photo Collection</h1>
                <div className="flex flex-row w-full justify-center space-x-20">
                    <Figure src={"/proj1/gallery/self_portrait_original.jpg"}
                        caption={"Prokudin-Gorskii's self-portrait before aligning"}
                        loading="eager"
                    />
                    <Figure
                        src={"/proj1/gallery/self_portrait_canny_out.jpg"}
                        caption={"My auto-aligned glass plates of Prokudin-Gorskii's self-portrait"}
                        loading="eager"
                    />
                </div>
                <section id="context" className="space-y-5">
                    <h2 className="font-medium">Background Context</h2>
                    <p>
                        Almost all 21st-century electronic displays use RGB to display color!
                        In the RGB color model, red, green, and blue primary colors of light are added together to form the full spectrum of human-visible colors.
                        The reason that red, green, and blue were specifically chosen actually has to do with the physiology of the human eye!
                        Humans have 2 kinds of light-sensitive receptor cells in their eyes: cones and rods.
                        Cones are responsible for color vision, and most humans have 3 kinds of cones: S, M, and L cones.
                        S stands for "short" wavelength, M stands for "medium" wavelength, and L stands for "long" wavelengths.
                        We perceive different wavelengths of light between 400nm and 700nm as different colors.
                        The S cone is most sensitive to light with a wavelength of 440nm (the color blue!).
                        The M cone's light sensitivity peak is 530nm (the color green).
                        And lastly, the L cone's light sensitivity peak is 560nm (the color red).

                        So the RGB model directly corresponds to the 3 colors our eyes are most sensitive to!
                    </p>
                    <p>
                        Although Sergei Mikhailovich Prokudin-Gorskii (1863-1944) didn't have access to color photography and electronic
                        displays like we do, he had the <em>foresight</em> to preserve the Russian Empire of the early 20th century using color.
                        From c. 1905-1915, he took thousands of photographs by using red, green, and blue filters to capture 3 different exposures of every scene.
                        <br />
                        In 1948, the Library of Congress purchased Prokudin-Gorskii's RGB glass plate negatives.
                        From 2000-2004, the LoC scanned Prokudin-Gorskii's glass plates and made them publicly accessible online.
                    </p>
                    <p>
                        Each glass plate image only captures the intensities of either red, green, or blue light.
                        By stacking the glass plates on top of each other and coloring them, the reds, greens, and blues add together to produce a full color image!

                        However, even though Prokudin-Gorskii's glass plates were exposures of the same scene, the subjects of each plate don't always line up exactly.
                        Naively stacking the plates can result in a final image with blurry edges and colorful ghosts.
                    </p>
                    <p>
                        In this project, I explored different ways to automatically align the colored glass plates on top of each other in order to minimize visual artifacts.
                    </p>
                </section>
                <section id="overview" className="space-y-5">
                    <h2 className="font-medium">Overview</h2>
                    <p className="mb-3">
                        From a high-level birds-eye-view, my automatic image alignment function follows these steps:
                    </p>
                    <ul className="space-y-3">
                        <li>
                            - Takes a digitized image of the blue, green, and red glass plates joined together (sort of like a photostrip),
                            and splits it into 3 equal parts.</li>
                        <li>
                            - (Bells and whistle) Pre-processes each of the 3 color plates, such as by cropping away the black and white borders
                            on each plate produced as a side-effect of digital scanning.
                        </li>
                        <li>
                            - Aligns the green plate to the blue plate by searching over a range of possible displacements <code>(dy, dx)</code> and
                            finding the displacement that optimizes some metric (e.g. L2 Norm between the pixel values of both plates or normalized-cross-correlation)
                            representing how well the images align together.
                        </li>
                        <li>
                            - Similarly, aligns the red plate to the blue plate by finding the displacement <code>(dy, dx)</code> that results in the best image alignment metric.
                        </li>
                        <li>
                            - Shifts the green plate by the best displacement found for aligning green to blue. Shifts the red plate by the best displacement found for aligning red to blue.
                            Then stacks all 3 color plates into a single image with 3 color channels.
                        </li>
                        <li>
                            - (Bells and whistles) Post-process the final color image after stacking, such as by trimming the edges of the
                            final image that don't correspond to pixels where the 3 color plates actually overlapped. For instance,
                            my implementation uses <code>np.roll</code> to shift the green and red plates after finding the optimal displacement vectors.
                            <code>np.roll</code> wraps pixels from one side to the opposite side, so sometimes certain pixels on the outer edges of the final
                            color image weren't actually in that location in the real scene — they've just been wrapped around to the other side.
                        </li>
                        <li>
                            - Gaze in wonder at the colors of the Russian Empire from over 100 years ago!
                        </li>
                    </ul>
                    <p className="mt-2">
                        The rest of this page will zoom in on the details :)
                    </p>
                </section>
                <section id="basic_alignment" className="space-y-5">
                    <h2 className="font-medium">Single-Scale Alignment</h2>
                    <p>
                        The simplest way to align the color plates is to search for the best alignment at a single scale/resolution of the color plates.
                        I implemented single-scale alignment using a double-nested for-loop that iterated through <code>(dy, dx)</code> pairs.
                        For each candidate displacement, I shifted one plate by the amount <code>(dy, dx)</code> — a positive dy displacement meant shifting
                        the plate DOWN by dy pixels, and a positive dx displacement meant shifting the plate RIGHT by dx pixels. I used this convention
                        to match up with how NumPy sets the origin (0, 0) as corresponding to the top-left corner of an image array, and how the first
                        index in the tuple (i, j) describing the location of the (i, j)-th pixel corresponds to that pixels' row location and the second index
                        corresponds to that pixel's column location.
                    </p>
                    <p>
                        After shifting one plate, I scored how well this candidate plate aligned with the base plate (in my implementation, I fixed BLUE as the
                        base plate and aligned red and green to the BLUE plate) using the following image matching metrics:
                    </p>
                    <p><b>L2 Norm AKA Euclidean Distance:</b> Compute the squared distance between the corresponding pixel values in the candidate image and the base image.
                        Sum the squared distances across all pixel positions. Then take the square root of the sum.
                        <br />
                        When using the L2 Norm to as the alignment metric, a <b>smaller</b> L2 norm is better (i.e. the plates are more aligned)!
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="L2 norm equals the square root of the sum of squared matrix or vector components"
                        dangerouslySetInnerHTML={{ __html: l2NormEquationRendered }}
                    />
                    <p><b>Normalized Cross-Correlation (NCC):</b> For each image, compute the mean of its pixel values. Center the image matrix by subtracting the mean element-wise
                        from every pixel in the matrix. Then compute the L2 norm of the mean-centered matrix.
                        Normalize by dividing every pixel by this L2 norm.
                        Finally, take the dot product between the two normalized matrices.
                        <br />
                        When using the NCC as the alignment metric, a <b>bigger</b> NCC is better (i.e. the plates are more aligned)!
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="Normalized cross-correlation"
                        dangerouslySetInnerHTML={{ __html: NCCEquationRendered }}
                    />
                    <p>NB: One way to apply these difference metrics to 2D image matrices instead of vectors is by unraveling the matrix into a long, 1-dimensional vector.</p>

                    <p>Here is a comparison of church.tif, whose best displacement vector differed the most between the two metrics (L2 Norm vs. NCC) among the 14 provided images.</p>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        <Figure src={"/proj1/church_original.jpg"} caption={"church.tif before automatic alignment"} />
                        <Figure src={"/proj1/church_l2.jpg"} caption={"church.tif aligned with L2 Norm"} subcaption={"red (dy, dx): (58, 188), green (dy, dx): (25, 2)"} />
                        <Figure src={"/proj1/church_ncc.jpg"} caption={"church.tif aligned with NCC"} subcaption={"red (dy, dx): (57, -5), green (dy, dx): (24, 3)"} />
                    </div>
                    <section id="single_scale_gallery" className="space-y-5">
                        <h2 className="font-medium">Single-Scale Gallery</h2>
                        <p>
                            Using single-scale automatic alignment and searching over a range of [-15, 15] for dy and dx worked well on the smaller digitized glass plate data!
                            Here are the results of single-scale automatic alignment on the smaller images: cathedral.jpg, monastery.jpg, and tobolsk.jpg.
                        </p>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                            <Figure src={"/proj1/gallery/cathedral_original.jpg"} caption={"cathedral.jpg (original, dimensions: (341px, 390px))"} />
                            <Figure src={"/proj1/cathedral_single_scale_l2.jpg"} caption={"cathedral.jpg (single-scale + L2)"} subcaption={"red (dy, dx): (12, 3), green (dy, dx): (5, 2); total time: 0.218s"} />
                            <Figure src={"/proj1/cathedral_single_scale_ncc.jpg"} caption={"cathedral.jpg (single-scale + NCC)"} subcaption={"red (dy, dx): (12, 3), green (dy, dx): (5, 2); total time: 0.535s"} />

                            <Figure src={"/proj1/gallery/monastery_original.jpg"} caption={"monastery.jpg (original, dimensions: (341px, 391px))"} />
                            <Figure src={"/proj1/monastery_single_scale_l2.jpg"} caption={"monastery.jpg (single-scale + L2)"} subcaption={"red (dy, dx): (3, 2), green (dy, dx): (-3, 2); total time: 0.234s"} />
                            <Figure src={"/proj1/monastery_single_scale_ncc.jpg"} caption={"monastery.jpg (single-scale + NCC)"} subcaption={"red (dy, dx): (3, 2), green (dy, dx): (-3, 2); total time: 0.504s"} />

                            <Figure src={"/proj1/gallery/tobolsk_original.jpg"} caption={"tobolsk.jpg (original, dimensions: (341px, 396px))"} />
                            <Figure src={"/proj1/tobolsk_single_scale_l2.jpg"} caption={"tobolsk.jpg (single-scale + L2)"} subcaption={"red (dy, dx): (6, 3), green (dy, dx): (3, 2); total time: 0.225s"} />
                            <Figure src={"/proj1/tobolsk_single_scale_ncc.jpg"} caption={"tobolsk.jpg (single-scale + NCC)"} subcaption={"red (dy, dx): (6, 3), green (dy, dx): (3, 2); total time: 0.525s"} />
                        </div>
                    </section>
                    <p>
                        However, when trying to align hi-res glass plates where the each side is measured in thousands of pixels, the glass plates have much bigger
                        margins of displacement so we have to search over much larger windows for dy and dx. Instead of brute-force searching over hundreds or thousands of
                        displacements, automatic alignment can use image pyramids to hierarchically refine the best-estimate displacement at multiple scales!
                    </p>
                    <Figure src="/proj1/single_scale_vs_pyramid_time.jpg"
                        caption="The time in seconds it took the single-scale alignment algo to search the same window of possible displacements as the best displacements found by the image pyramid implementation" />
                </section>
                <section id="image_pyramids" className="space-y-5">
                    <h2 className="font-medium">Image Pyramids</h2>
                    <Figure
                        src={"https://thumb.wikimedia.org/wikipedia/commons/thumb/4/43/Image_pyramid.svg/1920px-Image_pyramid.svg.png"}
                        caption={"An image pyramid with 5 levels/resolution scales (source: Wikipedia)"}
                    />
                    <p>
                        An image pyramid is a strategy in image-processing algorithms where the image is scaled to different resolutions and processed hierarchically.
                        I incorporated image pyramids into my automatic alignment algorithm by recursively calling the automatic alignment algorithm on a downsampled
                        version of the color plate and the base plate, where each time I rescaled the dimensions by 1/2.
                        I set the base case to be when the plates shrunk down to a width or height of under 200 px.
                        At the base case, I simply performed a brute-force search over a window of [-15, 15] with (0, 0) as the initial estimate for the displacements <code>(dy, dx)</code>.
                        The base case returns a displacement vector <code>(dy, dx)</code> that represents the current best estimate for how to align the two plates at this coarse resolution.
                    </p>
                    <p>
                        Back in the recursive caller, I first scale the returned displacement vector <code>(dy, dx)</code> by 2x — the raw <code>(dy, dx)</code>
                        represents how much the downsampled plates with 1/2 the width and 1/2 the height should be displaced to align with each other.
                        Thus, these displacements should be scaled back up by a factor of 2x to correspond to the actual number of pixels that the
                        higher resolution plates would need to be shifted by.
                    </p>
                    <p>
                        The algorithm uses these scaled up displacement vectors as the centers for a new search neighborhood, this time with a smaller, more manageable search radius for dy and dx.
                        If the algorithm finds a displacement with a better alignment metric during the course of searching in this new neighborhood, it saves
                        the updated displacements.


                        Finally, the algorithm returns the best displacements it's found so far after refining the initial estimates.
                    </p>
                    <p>
                        This continues recursively back up the call stack until control flow returns back to the first automatic alignment function call, with
                        the plates at their original, full dimensions.
                    </p>
                    <p className="mb-3">
                        Of course, an image is worth a thousand coding experiments!
                        Here are some additional features I implemented in my image pyramid automatic alignment algorithm to #makeitwork.
                    </p>
                    <ul className="space-y-3">
                        <li>
                            - <b>Ignoring the margins of the plates in the displacement search sub-function: </b>
                            I observed that for many of the images, all 3 color plates had noticeable black or white borders.
                            Since the pixel values are mostly the same for all 3 color plates along these borders, it's likely that
                            the similarity of these pixels on the border would dominate the alignment metrics even though they don't
                            provide useful signal for actually aligning the most important visual subjects in the scene. Therefore,
                            in my displacement search sub-function, I included an adjustable margin to crop off from all 4 sides of the
                            two plates before searching to remove the influence of these low-signal borders on the metric.
                        </li>
                        <li>
                            - <b>Scoring the interior region of the two plates rather than the full image: </b>
                            I hypothesized that most of the most useful signal for aligning the two plates together would be in the center of the image,
                            away from the edges which could contain extraneous artifacts as a result of preservation or scanning.
                            At the same time, scoring the largest interior rectangle possible would allow my algorithm to compare
                            the largest proportion of pixels between the two plates for matches.
                            < br />< br />
                            So before searching, I first computed the largest possible interior rectangle from the base plate.
                            < br />< br />
                            I knew that given initial displacements <code>(dy_center, dx_center)</code> and radii <code>(dy_radius, dx_radius)</code>, the algorithm would shift
                            the other plate by some vertical displacement within the range <code>[dy_center - dy_radius, dy_center + dy_radius]</code> and by some
                            horizontal displacement within the range <code>[dx_center - dx_radius, dx_center + dx_radius]</code>.
                            < br />< br />
                            Based on this heuristic, I calculated left edges, right edges, top edges, and bottom edges of the base plate's interior rectangle
                            such that even if the algo shifted the other plate, the regions of the shifted plate that would now be located on top of the
                            chosen rectangle from the base plate would still be within bounds of the shifted plate; and therefore I could
                            slice out a corresponding rectangle from the shifted plate to compare with the base plate's interior rectangle without going out of bounds.
                            < br />< br />
                            For instance, assume that the rectangle from the base plate has the following coordinates: y0 (top edge), y1 (bottom edge), x0 (left edge), and x1 (right edge).
                            This rectangle can be extracted from the base plate as follows: <code>base_plate[y0:y1, x0:x1]</code>.
                            Also assume that the other color plate is being shifted by <code><code>(dy, dx)</code></code>, where positive dy is a shift downwards and positive dx is a shift rightwards.
                            Then the pixels from the other color plate that are now mapped on top of the base plate's chosen rectangle are <code>plate[y0 - dy : y1 - dy, x0 - dx : x1 - dx]</code>.
                            Thus, I needed to make sure that this change-of-coordinates always stayed within bounds of the other color plate, and also didn't
                            index into the ignored margins!
                        </li>
                        <li>
                            - <b>Trimming non-overlapping pixels from the edges of the final color image after all plates were stacked: </b>
                            When using <code>np.roll</code> to shift the pixels of the G and R plates, sometimes the pixels on one edge are wrapped around to the opposite edge.
                            As a result, the edges of the final color image might contain some pixels which were actually on the opposite side of the real scene.
                            I use the displacement vectors for the G plates and R plates to calculate the smallest margin I can trim away on each of the 4 sides
                            of the final stacked iamge to remove these non-sequitur pixels.
                        </li>
                    </ul>
                </section>
                <section id="bells_and_whistles" className="space-y-5">
                    <h2 className="font-medium">Bells and Whistles!</h2>
                    <p>
                        <b>Automatic cropping and detecting solid-color borders: </b> Before aligning the color plates to one another, I cropped the white and black borders from all 3 plates.
                        To detect whether a row or column should be cropped, I computed the fraction of elements in a given row/column whose pixel values were within
                        a tolerance of 0.1 from 1.0 (white) or 0.1 (an approximation for black). As long as more than 70% of the pixels in this row/column were the target color,
                        the algorithm considered them part of the solid-color border. The algorithm would then continue scanning inwards until it found a row/column where less than
                        70% of the pixels were within tolerance of the solid-color border, or until it hit a max crop limit of 5% of the full height/width.
                    </p>
                    <p>
                        One example where cropping the black and white borders first before aligning significantly improved the quality of the final alignment
                        was church.tif. In the result without first cropping B/W borders, the edges of the church are visibly misaligned.

                        Cropping the B/W borders first removes the aligned image's visual artifacts, and results in a different green displacement vector.
                    </p>
                    <div className="grid grid-cols-1 gap-4 pt-10 md:grid-cols-3">
                        <Figure
                            src="/proj1/gallery/church_original.jpg"
                            caption="church.tif (original)"
                        />
                        <Figure
                            src="/proj1/gallery/church_wo_bw_border_crop_out.jpg"
                            caption="church.tif (image pyramid + NCC, no B/W border cropping)"
                            subcaption="red (dy, dx): (57, -5), green (dy, dx): (-1, -5)"
                        />
                        <Figure
                            src="/proj1/gallery/church_ncc_out.jpg"
                            caption="church.tif (image pyramid + NCC + B/W border cropping)"
                            subcaption="red (dy, dx): (57, -5), green (dy, dx): (24, 3)"
                        />
                    </div>
                    <p>
                        <b>Automatic edge detection using Canny edge detectors: </b> Even with all the automatic alignment tricks I threw at it so far, emir.tif evaded alignment!
                        Aligning based on pixel intensity alone proved insufficient because Emir's robe is overwhelmingly blue. The pixel values of his robe in the red and green
                        plates are much darker compared to to the blue plate; hence, L2 norm and NCC will struggle to align his robe's red or green pixels to the blue pixels since their values differ so much!
                        The solution I explore was to align the color plates based on edges of objects, people, or scenery instead!
                        Since the three color plates all captured the same scene at roughly the same moment in time, the shapes in the scene were more consistent than color, especially if one color dominates the other two in a particular spot.

                        I used scikit-image's Canny edge detector. Canny edge detection is a multi-stage algorithm that detects edges by convolving the image with a Gaussian filters to remove noise and taking the gradient of the image to compute
                        how the image's pixel intensities change in a local window. The intensity of the image gradient can be used to identify edges.
                    </p>
                    <p>
                        Below, you can see how edge detection greatly improved the final alignment quality of Emir's portrait!

                        For the other provided images, automatic alignment based on pixel intensities vs. edges produced roughly the same displacements.
                    </p>
                    <div className="grid grid-cols-1 gap-4 pt-10 md:grid-cols-3">
                        <Figure
                            src="/proj1/gallery/emir_original.jpg"
                            caption="emir.tif (original)"
                        />
                        <Figure
                            src="/proj1/gallery/emir_ncc_out.jpg"
                            caption="emir.tif (image pyramid + NCC + B/W border cropping)"
                            subcaption="red (dy, dx): (132, -276), green (dy, dx): (49, 24)"
                        />
                        <Figure
                            src="/proj1/gallery/emir_canny_out.jpg"
                            caption="emir.tif (image pyramid + Canny + NCC + B/W border cropping)"
                            subcaption="red (dy, dx): (107, 40), green (dy, dx): (49, 23)"
                        />
                    </div>
                </section>
                <section id="timing_comparison" className="space-y-5">
                    <h2 className="font-medium">Alignment Timing Comparison</h2>
                    <div className="overflow-x-auto flex flex-col gap-4">
                        <p>I measured the time that it took 3 of my alignment algorithms to run.
                            This table contains the total seconds it took to align both the red and green plates to the blue plate
                            using the single-scale alignment algorithm, the image pyramid alignment algorithm on raw pixel values, or
                            the image pyramid alignment algorithm on edges from the Canny edge detector.
                            All 3 variations used NCC as the alignment metric.

                            These times represent the core algorithm, and do not include B/W border edge cropping or trimming wrap-around pixels.
                        </p>
                        <table className="w-full border-collapse text-sm mt-8">
                            <caption className="mb-3 text-left font-medium">
                                Core alignment runtime comparison (seconds)
                            </caption>
                            <thead>
                                <tr className="border-b border-gray-300">
                                    <th scope="col" className="px-3 py-2 text-left font-medium">Image</th>
                                    <th scope="col" className="px-3 py-2 text-right font-medium">Single-scale</th>
                                    <th scope="col" className="px-3 py-2 text-right font-medium">Image pyramid</th>
                                    <th scope="col" className="px-3 py-2 text-right font-medium">Image pyramid + Canny</th>
                                </tr>
                            </thead>
                            <tbody>
                                {galleryImages.map(({ stem, filename, nccTime, cannyTime }) => (
                                    <tr key={stem} className="border-b border-gray-200 last:border-0">
                                        <th scope="row" className="px-3 py-2 text-left font-normal">{filename}</th>
                                        <td className="px-3 py-2 text-right tabular-nums">{singleScaleTimes[stem].toFixed(3)}</td>
                                        <td className="px-3 py-2 text-right tabular-nums">{nccTime.toFixed(3)}</td>
                                        <td className="px-3 py-2 text-right tabular-nums">{cannyTime.toFixed(3)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
                <section id="final_results_gallery" className="space-y-5">
                    <h2 className="font-medium">Final Results Gallery</h2>
                    <p>Here are the final results of my automatic alignment algorithm on 14 provided glass plate images,
                        plus 4 pictures I chose from the Library of Congress's Prokudin-Gorskii online collection:{" "}
                        <a href="https://www.loc.gov/item/2018679239/" target="_blank" rel="noopener noreferrer" className="text-[var(--color-code-blue)] hover:underline">laika.tif</a>,{" "}
                        <a href="https://www.loc.gov/item/2018679122/" target="_blank" rel="noopener noreferrer" className="text-[var(--color-code-blue)] hover:underline">milan_duomo.tif</a>,{" "}
                        <a href="https://www.loc.gov/item/2018679978/" target="_blank" rel="noopener noreferrer" className="text-[var(--color-code-blue)] hover:underline">borodino.tif</a>, and{" "}
                        <a href="https://www.loc.gov/item/2018678884/" target="_blank" rel="noopener noreferrer" className="text-[var(--color-code-blue)] hover:underline">st_boris.tif</a>!
                    </p>
                    <p>
                        These were all processed by first splitting the image data into red, green, and blue plates;
                        cropping solid-color borders from each of the glass plates;
                        aligning the red plate to the blue plate using my image pyramid alignment algorithm;
                        aligning the green plate to the blue plate using my image pyramid alignment algorithm;
                        stacking the 3 aligned plates together into a 3-channel color image;
                        and lastly, trimming the misplaced, wrap-around pixels from the edges.

                        I included 5 variations for every image:
                        - original: stacking the 3 color plates after splitting without any alignment
                        - image pyramid + NCC, no B/W border cropping: all the steps except cropping solid-color borders before aligning.
                        This serves as a comparison for my bells and whistles feature: "Automaic cropping and detecting solid-color borders".
                        - image pyramid + L2 + B/W border cropping: all the steps, with plate alignment search measured based on the L2 distance
                        - image pyramid + NCC + B/W border cropping: all the steps, with plate alignment search measured based on NCC
                        - image pyramid + Canny + NCC + B/W border cropping: all the steps, with alignment search performed on each color plate's detected edges
                        rather than their raw pixel values.
                    </p>
                    <p>
                        Overall, I found cropping solid-color borders and using NCC produced higher quality alignments.
                        Edge detection most noticeably improved the quality of emir.tif, but found pretty similar best displacements for most of the other images.
                    </p>
                    <div className="space-y-10">
                        {galleryImages.map(({ stem, filename, noBorderCrop, l2, ncc, canny }) => (
                            <div key={stem} className="space-y-4">
                                <div className="flex flex-col justify-center gap-20 md:flex-row">
                                    <Figure
                                        src={`/proj1/gallery/${stem}_original.jpg`}
                                        caption={`${filename} (original)`}
                                        style_width={"20vw"}
                                    />
                                    <Figure
                                        src={`/proj1/gallery/${stem}_wo_bw_border_crop_out.jpg`}
                                        caption={`${filename} (image pyramid + NCC, no B/W border cropping)`}
                                        subcaption={noBorderCrop}
                                        style_width={"20vw"}
                                    />
                                </div>
                                <div className="grid grid-cols-1 justify-items-center gap-4 md:grid-cols-3">
                                    <Figure
                                        src={`/proj1/gallery/${stem}_l2_out.jpg`}
                                        caption={`${filename} (image pyramid + L2 + B/W border cropping)`}
                                        subcaption={l2}
                                        style_width={"20vw"}
                                    />
                                    <Figure
                                        src={`/proj1/gallery/${stem}_ncc_out.jpg`}
                                        caption={`${filename} (image pyramid + NCC + B/W border cropping)`}
                                        subcaption={ncc}
                                        style_width={"20vw"}
                                    />
                                    <Figure
                                        src={`/proj1/gallery/${stem}_canny_out.jpg`}
                                        caption={`${filename} (image pyramid + Canny + NCC + B/W border cropping)`}
                                        subcaption={canny}
                                        style_width={"20vw"}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                    <section id="additional_images" className="space-y-5">
                        <h3 className="font-medium">Additional Images</h3>
                        {additionalGalleryImages.map(({ stem, filename, noBorderCrop, l2, ncc, canny }) => (
                            <div key={stem} className="space-y-4">
                                <div className="flex flex-col justify-center gap-4 md:flex-row">
                                    <Figure
                                        src={`/proj1/gallery/${stem}_original.jpg`}
                                        caption={`${filename} (original)`}
                                        style_width={"20vw"}
                                    />
                                    <Figure
                                        src={`/proj1/gallery/${stem}_wo_bw_border_crop_out.jpg`}
                                        caption={`${filename} (image pyramid + NCC, no B/W border cropping)`}
                                        subcaption={noBorderCrop}
                                        style_width={"20vw"}
                                    />
                                </div>
                                <div className="grid grid-cols-1 justify-items-center gap-4 md:grid-cols-3">
                                    <Figure
                                        src={`/proj1/gallery/${stem}_l2_out.jpg`}
                                        caption={`${filename} (image pyramid + L2 + B/W border cropping)`}
                                        subcaption={l2}
                                        style_width={"20vw"}
                                    />
                                    <Figure
                                        src={`/proj1/gallery/${stem}_ncc_out.jpg`}
                                        caption={`${filename} (image pyramid + NCC + B/W border cropping)`}
                                        subcaption={ncc}
                                        style_width={"20vw"}
                                    />
                                    <Figure
                                        src={`/proj1/gallery/${stem}_canny_out.jpg`}
                                        caption={`${filename} (image pyramid + Canny + NCC + B/W border cropping)`}
                                        subcaption={canny}
                                        style_width={"20vw"}
                                    />
                                </div>
                            </div>
                        ))}
                    </section>
                </section>
            </article>
            <aside className="fixed right-0 top-20 hidden h-fit max-h-[70vh] w-[15vw] min-w-[150px] px-4 overflow-y-auto border-l-2 border-gray-200 md:block">
                <TableOfContents contents={contents} />
            </aside>
        </main>
    );
}
