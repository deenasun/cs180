"use client";

import katex from "katex";
import "katex/dist/katex.min.css";

import Image from "next/image";
import TableOfContents from "@/components/TableOfContents";
import { getAssetPath } from "@/shared"


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
            sectionLink: "image_pyramids",
            text: "Image Pyramids"
        },
        {
            sectionLink: "bells_and_whistles",
            text: "Bells and Whistles"
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
                    <Image
                        key={"self_portrait_original"}
                        src={getAssetPath("/proj1/self_portrait_original.jpg")}
                        alt={"Prokudin-Gorskii's self-portrait before aligning the colorized glass plates"}
                        height={1080}
                        width={1080}
                        style={{ width: "25vw", height: 'auto' }}
                    />
                    <Image
                        key={"self_portrait_aligned"}
                        src={getAssetPath("/proj1/self_portrait_out.jpg")}
                        alt={"Prokudin-Gorskii's self-portrait after cropping black/white edges and aligning using image pyramids"}
                        height={1080}
                        width={1080}
                        style={{ width: "25vw", height: 'auto' }}
                    />
                </div>
                <section id="context" className="space-y-5">
                    <h2 className="font-medium">Background Context</h2>
                    <p>
                        RGB is the ubiquitous color model used by 21st-century electronic devices to display color.
                        In the RGB color model, red, green, and blue primary colors of light are added together to form the full spectrum of human-visible colors.
                        The reason that red, green, and blue were specifically chosen actually has to do with the physiology of the human eye!
                        Humans have 2 kinds of light-sensitive receptor cells in their eyes: cones and rods.
                        Cones are responsible for color vision, and most humans have 3 kinds of cones: S, M, and L cones.
                        S stands for "short" wavelength, M stands for "medium" wavelength, and L stands for "long" wavelengths.
                        We perceive different wavelengths of light between 400 nm and 700 nm as different colors.
                        The S cone is most sensitive to light with a wavelength of 440 nm (the color blue!).
                        The M cone's light sensitivity peak is 530 nm (the color green).
                        And lastly, the L cone's light sensitivity peak is 560 nm (the color red).

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
                            - Aligns the green plate to the blue plate by searching over a range of possible displacements (dy, dx)
                            and finding the displacement that optimizes some metric (e.g. L2 Norm between the pixel values of both plates or normalized-cross-correlation)
                            representing how well the images align together.
                        </li>
                        <li>
                            - Similarly, aligns the red plate to the blue plate by finding the displacement (dy, dx) that results in the best image alignment metric.
                        </li>
                        <li>
                            - Shifts the green plate by the best displacement found for aligning green to blue. Shifts the red plate by the best displacement found for aligning red to blue.
                            Then stacks all 3 color plates into a single image with 3 color channels.
                        </li>
                        <li>
                            - (Bells and whistles) Post-process the final color image after stacking, such as by trimming the edges of the
                            final image that don't correspond to pixels where the 3 color plates actually overlapped. For instance,
                            my implementation uses np.roll to shift the green and red plates after finding the optimal displacement vectors.
                            np.roll wraps pixels from one side to the opposite side, so sometimes certain pixels on the outer edges of the final
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
                        I implemented single-scale alignment using a double-nested for-loop that iterated through (dy, dx) pairs.
                        For each candidate displacement, I shifted one plate by the amount (dy, dx) — a positive dy displacement meant shifting
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

                </section>
                <section id="image_pyramids"><h2 className="font-medium">Image Pyramids</h2></section>
                <section id="bells_and_whistles"><h2 className="font-medium">Bells and Whistles!</h2></section>
            </article>

            <aside className="fixed right-0 top-20 hidden h-fit max-h-[70vh] w-[15vw] min-w-[150px] px-4 overflow-y-auto border-l-2 border-gray-200 md:block">
                <TableOfContents contents={contents} />
            </aside>
        </main>
    );
}