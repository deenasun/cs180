import Equation from "@/components/Equation";
import Figure from "@/components/Figure";
import TableOfContents from "@/components/TableOfContents";


export default function Page() {
    const contents = [
        {
            sectionLink: "part_a_1",
            text: "Part A.1: Shoot the Pictures"
        },
        {
            sectionLink: "part_a_2",
            text: "Part A.2: Recover Homographies"
        },
        {
            sectionLink: "part_a_3",
            text: "Part A.3: Warp the Images"
        },
        {
            sectionLink: "part_a_4",
            text: "A.4: Blend the Images into a Mosaic"
        },
        {
            sectionLink: "part_b_1",
            text: "Part B.1: Harris Corner Detection"
        },
        {
            sectionLink: "part_b_2",
            text: "Part B.2: Feature Descriptor Extraction"
        },
        {
            sectionLink: "part_b_3",
            text: "Part B.3: Feature Matching"
        },
        {
            sectionLink: "part_b_4",
            text: "B.4: RANSAC for Robust Homography"
        },

    ]
    return (
        <main className="mx-4 my-2 sm:mx-8">
            <article className="mr-[17vw] space-y-12">
                <h1 className="font-bold">Project 4: Autostitching Photo Mosaics</h1>
                <div className="flex flex-row w-full justify-center space-x-20">
                    <Figure
                        src={"/proj4/part_a/campus_mosaic.jpg"}
                        caption={"A mosaic of the Berkeley campus!"}
                        style_width="50vw"
                        loading="eager"
                    />
                </div>
                <section id="part_a_1" className="space-y-5">
                    <h2 className="font-medium">Part A.1: Shooting the Pictures</h2>
                    <p>First, I captured a few sets of photographs of the same scene by rotating a camera while trying to keep its center of projection fixed.
                        This results in photographs which can be transformed into one another via a projective transform.
                    </p>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        <Figure
                            src={"/proj4/part_a/gec_1.jpg"}
                            caption={"Image 1 of the Grimes Engineering Center"}
                            style_width="10vw"
                        />
                        <Figure
                            src={"/proj4/part_a/gec_2.jpg"}
                            caption={"Image 2 of the Grimes Engineering Center"}
                            style_width="10vw"
                        />
                        <Figure
                            src={"/proj4/part_a/gec_3.jpg"}
                            caption={"Image 3 of the Grimes Engineering Center"}
                            style_width="10vw"
                        />
                    </div>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        <Figure
                            src={"/proj4/part_a/campus_1.jpg"}
                            caption={"Image 1 of the Berkeley campus"}
                            style_width="10vw"
                        />
                        <Figure
                            src={"/proj4/part_a/campus_2.jpg"}
                            caption={"Image 2 of the Berkeley campus"}
                            style_width="10vw"
                        />
                        <Figure
                            src={"/proj4/part_a/campus_3.jpg"}
                            caption={"Image 3 of the Berkeley campus"}
                            style_width="10vw"
                        />
                        <Figure
                            src={"/proj4/part_a/campus_4.jpg"}
                            caption={"Image 4 of the Berkeley campus"}
                            style_width="10vw"
                        />
                        <Figure
                            src={"/proj4/part_a/campus_5.jpg"}
                            caption={"Image 5 of the Berkeley campus"}
                            style_width="10vw"
                        />
                    </div>
                </section>
                <section id="part_a_2" className="space-y-5">
                    <h2 className="font-medium">Part A.2: Recover Homographies</h2>
                    <p>Next, I needed to find the transformation matrix H which could be applied to one image in order to
                        warp it onto a shared projective plane as the second image.

                        In this case, the transformation matrix is a homography matrix H with dimensions (3, 3) and 8 degrees of freedom
                        (the lower right element is a scaling factor that can be set to 1).
                        {"\n\n"}
                        A correspondence is a pair of pixel points (p', p) in two images that represent the same
                        point in the 3D world.
                        {"\n\n"}
                        Given a point p' in image 1 and a point p in image 2, left-multiplying the homogeneous coordinates of p by H maps it to p'.
                        Dividing the resulting 3D vector by its last component to normalize it into a homogeneous coordinate
                        with depth 1 gives:
                    </p>
                    <Equation
                        rawString={String.raw`\begin{align*}
                            \begin{bmatrix}
                            x'\\
                            y'\\
                            1
                            \end{bmatrix}
                            &= \begin{bmatrix}
                                a & b & c \\
                                d & e & f \\
                                g & h & 1
                                \end{bmatrix}
                            \begin{bmatrix}
                            x\\
                            y\\
                            1
                            \end{bmatrix}
                            \\ \\
                            &= \begin{bmatrix}
                                (ax + by + c) \\
                                (dx + ey + f) \\
                                (gx + hy + 1)
                                \end{bmatrix}
                            \\ \\
                            &= \begin{bmatrix}
                                \frac{(ax + by + c)}{(gx + hy + 1)} \\ \\
                                \frac{(dx + ey + f)}{(gx + hy + 1)} \\ \\
                                1
                                \end{bmatrix}
                            \end{align*}`}
                        ariaLabel="Homography transformation between a pair of points."
                    />
                    <p>
                        Looking at just the non-homogeneous coordinates:
                    </p>
                    <Equation
                        rawString={String.raw`\begin{align*}
                            x' \cdot  (gx + hy + 1) = ax + by + c, \\
                            y' \cdot (gx + hy + 1) = dx + ey + f
                            \end{align*}`}
                        ariaLabel="Homography transformation between a pair of points."
                    />
                    <p>
                        Rewriting the equations to isolate x' and y' on the left-hand side:
                    </p>
                    <Equation
                        rawString={String.raw`\begin{align*}
                            x' = ax + by + c - x' \cdot gx - x' \cdot hy \\
                            y' = dx + ey + f - y' \cdot gx - y' \cdot hy
                            \end{align*}`}
                        ariaLabel="Homography transformation between a pair of points."
                    />
                    <p>
                        Therefore, pair of points (p', p) gives us 2 equations.
                        Since H has 8 degrees of freedom, we need at least 4 pairs of points to have a determined system of equations.
                        Then, we will be able to set up a linear system of equations in the form of Ah=b, where h is a 8D vector holding
                        the 8 entries of H.
                    </p>
                    <Equation
                        rawString={String.raw`
                            \begin{bmatrix}
                            x'_1 \\
                            y'_1 \\
                            x'_2 \\
                            y'_2 \\
                            \vdots \\
                            x'_n \\
                            y'_n \\
                            \end{bmatrix}
                            =
                            \begin{bmatrix}
                            x_1 & y_1 & 1 & 0 & 0 & 0 & -x'_1 \cdot x_1 & -x'_1 \cdot y_1 \\
                            0 & 0 & 0 & x_1 & y_1 & 1 & -y'_1 \cdot x_1 & -y'_1 \cdot y_1 \\
                            x_2 & y_2 & 1 & 0 & 0 & 0 & -x'_2 \cdot x_2 & -x'_2 \cdot y_2 \\
                            0 & 0 & 0 & x_2 & y_2 & 1 & -y'_2 \cdot x_2 & -y'_2 \cdot y_2 \\
                            &&&& \vdots \\
                            x_n & y_n & 1 & 0 & 0 & 0 & -x'_n \cdot x_n & -x'_n \cdot y_n \\
                            0 & 0 & 0 & x_n & y_n & 1 & -y'_n \cdot x_n & -y'_n \cdot y_n \\
                            \end{bmatrix}
                            \begin{bmatrix}
                            a \\
                            b \\ 
                            c \\
                            d \\
                            e \\
                            f \\
                            g \\
                            h \\
                            \end{bmatrix}
                            `}
                        ariaLabel="Homography transformation between a pair of points."
                    />
                    <p>
                        The solution h will be unstable and prone to noise with only 4 points because an error of just a couple of pixels
                        can result in very big changes in the recoevered homography. Thus & it's useful to instead use more than 4
                        point pairs, creating an over-determined system of equations, then find an h via least-squares.
                        {"\n\n"}
                        In part A, I found correspondences between 2 images by implementing my own interactive widget that shows
                        two images side-by-side and lets users select points in each image.
                    </p>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        TODO: screenshot of the interactive window for finding correspondences.
                        TODO: show correspondences visualized on the images.
                        TODO: show the system of equations and recovered homography matrix.
                    </div>
                </section>
                <section id="part_a_3" className="space-y-5">
                    <h2 className="font-medium">Part A.3: Warp the Images</h2>
                    <p>
                        After recovering the homography, I warped one image onto another "reference" image's projective plane.
                        I implemented this via inverse warping! First, I computed what the pixel positions of image 1's corners would be
                        after warping. I used this as the bounding box to create an empty "canvas" of all zeros.
                        Then, I iterated through all the pixel positions in the canvas.
                        For each pixel position, I applied the inverse of the homography matrix to find which pixels in the
                        source image it came from. Then, I "gathered" the values from the source pixels and set the output pixel
                        to the gathered colors.
                        {"\n\n"}
                        I implemented 2 interpolation methods from scratch:
                        <ul>
                            <li><b>Nearest neighbor interpolation:</b> after inverting the output pixel coordinates, I rounded the resulting
                                coordinates to find the nearest, valid source pixel position to gather a value from.</li>
                            <li>
                                <b>Bilinear interpolation:</b> after inverting the output pixel coordinates, I computed the coordinates of the
                                4 neighboring pixels from the source image around the inverted coordinate, then used a weighted average of the
                                neighbors' values in the output based on how close the inverted pixel coordinate is to each neighbor.
                                To determine how much to weigh each neighbor's values, we can visualizethe neighbors as forming a 1 pixel by 1 pixel square.
                                The inverted pixel coordinates fall somewhere inside this square (possibly on an edge of the square or on
                                one of the neighbors themselves). The inverted pixel splits the 1x1 square into 4 sub-rectangles (or fewer than 4
                                sub-rectangles if the inverted pixel lies on an outer edge/corner). Then, each neighbor should be assigned
                                a weight proportional to the area of the sub-rectangle diagonal from it. For example, the
                                neighbor above and to the left of the inverted pixel should be weighted by an amount proportional to the area of
                                the bottom-right sub-rectangle.</li>
                        </ul>
                        For both interpolation methods, if the pixel in the warped output canvas was inverted to a coordinate that would be out-of-bounds
                        in the source image, I treated that source pixel as having a value or weight of 0.
                    </p>
                    <p>
                        To test my homography and interpolation code, I applied them to pictures depicting known rectangular objects from non-front-on angles.
                        This is known as "rectification": projecting images onto a common image plane (in this case, projecting images onto an plane such that
                        the skewed rectangular objects look like rectangle again).

                        Here are the results of rectifying XYZ. I knew that in real-life, these facades and paintings are rectangles with right angles and parallel edges.
                        But because the images were taken from an angle, the facades/paintings look like skewed quadrilaterals. Thus, rectifying these images involves
                        pairing these images with a placeholder image of a normal rectangle to represent a projective plane that views the facades/paintings from front-on,
                        computing a homography, and interpolating
                    </p>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        TODO: show rectifications on 2+ images.
                    </div>
                </section>
                <section id="part_a_4" className="space-y-5">
                    <h2 className="font-medium">Part A.4: Blend the Images into a Mosaic</h2>
                    <p>
                        With all these puzzle pieces in place, we can now stitch multiple overlapping images into an image mosaic!
                        In my implementation, I treated the middle image as the center of the mosaic, then transformed all the other images
                        onto this center image's projective plane. To avoid edge effects, I used multi-resolution blending with Laplacian and Gaussian stacks.
                        <ol>
                            <li>
                                Find  correspondences between adjacent images and compute Homographies
                                that map adjacent images to each other.
                            </li>
                            <li>
                                Compose the transforms together to find a homography for each image that maps
                                it onto the shared, common projective plane (AKA the projective plane that the
                                center image uses).
                            </li>
                            <li>
                                Compute the size that the shared canvas should have so that it fits all the images
                                after they are tranformed. For each image, transform its 4 corners using the image-to-center homography.
                                Then, find the minimum x, minimum y, maximum x, and maximum y coordinates across all the warped corners.
                                The shared canvas needs to be able to fit the full range of x, y coordinates; thus the dimensions
                                of the final mosaic canvas should equal (maximum x - minimum x + 1, maximum y - minimum y + 1) pixels.
                            </li>
                            <li>
                                Warp each image onto its own copy of the canvas.
                                Using the same sized canvas helps simplify the multi-resolution blend step.
                                Also, create a mask for each iamge. The mask should have the same shape as the canvas
                                and have 1's where the warped image is located, and 0's elsewhere.
                            </li>
                            <li>
                                Blend all the image canvases together using multi-resolution blending!
                                This involves creating Laplacian stacks of all the canvases containing a single warped image
                                and Guassian stacks of all the masks. Then, merge each level by weighting each canvas's Laplacian
                                at that level by its mask's Gaussian at that level. Finally, collapse (add) the blends from all the levels together.
                            </li>
                        </ol>
                    </p>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        TODO: show 3 mosaics with source images.
                    </div>
                </section>
            </article>
            <aside className="fixed right-0 top-20 hidden h-fit max-h-[70vh] w-[15vw] min-w-[150px] px-4 overflow-y-auto border-l-2 border-gray-200 md:block">
                <TableOfContents contents={contents} />
            </aside>
        </main>
    );
}