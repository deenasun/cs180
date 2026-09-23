import katex from "katex";
import "katex/dist/katex.min.css";
import SyntaxHighlighter from "react-syntax-highlighter";

import Figure from "@/components/Figure";
import TableOfContents from "@/components/TableOfContents";

const ALPHA_UNICODE = "\u03B1"

export default function Page() {
    const contents = [
        {
            sectionLink: "part_1.1_convolutions",
            text: "Part 1.1: Convs from Scratch"
        },
        {
            sectionLink: "part_1.2_dfo",
            text: "Part 1.2: Finite Difference Operators"
        },
        {
            sectionLink: "part_1.3_dog",
            text: "Part 1.3: Derivative of Gaussians Part"
        },
        {
            sectionLink: "part_2.1_sharpening",
            text: "2.1: Image Sharpening"
        },
        {
            sectionLink: "part_2.2_hybrid",
            text: "Part 2.2: Hybrid Images"
        },
        {
            sectionLink: "part_2.3_stacks",
            text: "Part 2.3: Gaussian and Laplacian Stacks"
        },
        {
            sectionLink: "part_2.4_blend",
            text: "Part 2.4: Multiresolution Blending"
        },
    ]

    const convCode = `def convolve_2d(matrix, filter, quad_for_loop=False):
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
    
    return out`

    const convolutionShapeFormula = String.raw`D_{out} = \lfloor \frac{D_{in} - K + 2P}{S} \rfloor + 1`

    const convolutionShapeFormulaRendered = katex.renderToString(convolutionShapeFormula, {
        displayMode: true,
        throwOnError: false,
    });

    const Dx = String.raw`D_x = \begin{bmatrix}1 & 0 & -1 \end{bmatrix}`

    const DxRendered = katex.renderToString(Dx, {
        displayMode: true,
        throwOnError: false,
    });

    const Dy = String.raw`D_y = \begin{bmatrix}1 \\ 0 \\ -1 \end{bmatrix}`

    const DyRendered = katex.renderToString(Dy, {
        displayMode: true,
        throwOnError: false,
    });

    const boxFilter = String.raw`B = \frac{1}{81} \begin{bmatrix}
1 & \cdots &1 \\
\vdots & \ddots & \vdots \\
1  & \cdots & 1
\end{bmatrix}`

    const boxFilterRendered = katex.renderToString(boxFilter, {
        displayMode: true,
        throwOnError: false,
    });

    const gradient = String.raw`\nabla f = \begin{bmatrix} \frac{\partial f}{\partial x}, \frac{\partial f}{\partial y} \end{bmatrix}`

    const gradientRendered = katex.renderToString(gradient, {
        displayMode: true,
        throwOnError: false,
    });

    const gradientMagnitude = String.raw`\lVert \nabla f \rVert = \sqrt{ \left( \frac{\partial f}{\partial x} \right) ^2 + \left( \frac{\partial f}{\partial y} \right) ^2}`

    const gradientMagnitudeRendered = katex.renderToString(gradientMagnitude, {
        displayMode: true,
        throwOnError: false,
    });

    const derivativeTheoremOfConvolution = String.raw`\frac{\partial}{\partial x} \left( h * f \right) = \left( \frac{\partial}{\partial x} h \right) * f`

    const derivativeTheoremOfConvolutionRendered = katex.renderToString(derivativeTheoremOfConvolution, {
        displayMode: true,
        throwOnError: false,
    });

    const sharpeningFilter = String.raw`f + \alpha(f - f * g) = f * \left( (1 + \alpha) e - \alpha g \right)`

    const sharpeningFilterRendered = katex.renderToString(sharpeningFilter, {
        displayMode: true,
        throwOnError: false,
    });

    return (
        <main className="mx-4 my-2 sm:mx-8">
            <article className="mr-[17vw] space-y-12">
                <h1 className="font-bold">Project 2: Fun with Filters and Frequencies!</h1>
                <div className="flex flex-row w-full justify-center space-x-20">
                    <Figure src={"/proj2/multiresolution_blend_apple_orange.jpg"}
                        caption={"Multi-resolution blending with Laplacian and Gaussian stacks: Oraple"}
                        loading="eager"
                        style_width="50vw"
                    />
                </div>
                <section id="part_1.1_convolutions" className="space-y-5">
                    <h2 className="font-medium">Part 1.1: Convolutions from Scratch</h2>
                    <p>A convolution takes a filter (AKA kernel) and slides it across an image. At every position, the filter is multiplied element-wise with
                        the pixels values of the image that it currently overlaps with.
                    </p>
                    <p>
                        I implemented a convolution from scratch using NumPy!
                        My homemade convolution:
                    </p>
                    <ul>
                        <li>- Calculates how many zero's to pad on the top, bottom, left, and right of the input image such that the output
                            of the convolution has the same dimensions as the input image (this is known as "same" padding!)</li>
                        <li>- Flips the filter</li>
                        <li>- Implements the convolution as a quadruple for-loop</li>
                        <li>- And implements the convolution as a double for-loop by taking advantage of NumPy's vectorized operations!</li>
                    </ul>
                    <p>As a very satisfying sanity check, I compared my hand-crafted convolution with <code>scipy.signal.convolve2d</code> to verify
                        that my implementation produced the exact same convolution outputs :)</p>
                    <p>
                        I handled the boundaries of my input images by same-padding with zeros so that the output would have the same dimensions as the input.
                        I calculated the right amount of padding to add on each side using the formula to calculate the dimensions of a convolution,
                        assuming stride (S) = 1, and finding the value of P that set D_out = D_in for both the width and height.
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="A formula to calculate the output dimensions of a convolution"
                        dangerouslySetInnerHTML={{ __html: convolutionShapeFormulaRendered }}
                    />

                    <p>
                        The runtime of my double for-loop is much faster than my quadruple for-loop, but both are outpaced by SciPy's convolution implementation!
                        SciPy's implementation includes optimizations like automatically switching between direct computations or a Fast Fourier Transform method
                        and using a compiled C/Fortran backend instead of Python's interpreter for small kernels.

                        Clearly there's a lot of engineering rabbit-holes to dive down to learn how to further optimize my handmade convolution!
                    </p>
                    <SyntaxHighlighter language="python">
                        {convCode}
                    </SyntaxHighlighter>
                    <p>I used my homemade convolution to convolve a grayscale image of myself with 3 different kernels/filters:</p>
                    <ul>
                        <li>- <b>Dx:</b> a finite difference filter that detects changes in the x-direction (vertical edges)</li>
                        <div
                            className="my-6 overflow-x-auto text-center"
                            aria-label="Dx is a finite difference filter that detects vertical edges when convolved with an image"
                            dangerouslySetInnerHTML={{ __html: DxRendered }}
                        />
                        <li>- <b>Dx:</b> a finite difference filter that detects changes in the y-direction (horizontal edges)</li>
                        <div
                            className="my-6 overflow-x-auto text-center"
                            aria-label="Dy is a finite difference filter that detects horizontal edges when convolved with an image"
                            dangerouslySetInnerHTML={{ __html: DyRendered }}
                        />
                        <li>- <b>Box filter:</b> an averaging filter that computes the average of all the pixels in a 9x9 neighrborhood.</li>
                        <div
                            className="my-6 overflow-x-auto text-center"
                            aria-label="Box filters average the pixel values"
                            dangerouslySetInnerHTML={{ __html: boxFilterRendered }}
                        />
                    </ul>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        <Figure
                            src={"/proj2/convolution_comparisons.jpg"}
                            caption={"Convolving a picture of myself with Dx, Dy, and a 9x9 box filter"}
                            loading="eager"
                            style_width="50vw"
                        />
                    </div>
                </section>
                <section id="part_1.2_fdo" className="space-y-5">
                    <h2 className="font-medium">Part 1.2: Finite Difference Operators</h2>
                    <p>By convolving an image with Dx or Dy, we can detect different kinds of edges!
                        Convolving an image with Dx detects vertical edges (i.e. changes in intensity between horizontally-adjacent pixels).
                        Likewise, convolving an image with Dy detects horizontal edges (i.e.changes in intensity between vertically-adjacent pixels).
                    </p>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <Figure
                            src={"/proj2/cameraman_conv_dx.jpg"}
                            caption={"Convolving camerman.jpg with Dx"}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj2/cameraman_conv_dy.jpg"}
                            caption={"Convolving camerman.jpg with Dy"}
                            style_width="50vw"
                        />
                    </div>
                    <p>The gradient is a vector of partial derivatives.
                        Therefore, the gradient of an image at each coordinate is a vector containing the corresponding pixels in the response after convolving the image with Dx and Dy.
                        Taking the magnitude of the gradient measures edge strength for all edge orientations in the image.
                        To better visualize the edges, I also binarized them: I identified all coordinates where the magnitude of the gradient at that position was above a certain threshold (found through visual trial and error),
                        then mapped those pixels to 1 and masked all other pixels to 0.
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="The gradient is a vector of partial derivatives"
                        dangerouslySetInnerHTML={{ __html: gradientRendered }}
                    />
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="A formula for the magnitude of the gradient"
                        dangerouslySetInnerHTML={{ __html: gradientMagnitudeRendered }}
                    />
                    <div className="grid grid-cols-1 gap-4 items-center md:grid-cols-2 ">
                        <Figure
                            src={"/proj2/cameraman_binarized_edge_magnitude.jpg"}
                            caption={"Edge strengths (binarized) of cameraman.jpg"}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj2/cameraman_finite_difference_operators.jpg"}
                            caption={"Comparing the results of convolving cameraman.jpg with finite difference operators"}
                            style_width="50vw"
                        />
                    </div>
                </section>
                <section id="part_1.3_dog" className="space-y-5">
                    <h2 className="font-medium">Part 1.3: Derivative of Gaussian Filter</h2>
                    <p>Directly convolving the image with finite difference operator filters can result in noisy edges.
                        To reduce noisiness, I first blurred camerman.jpg by convolving it with a Gaussian filter before convolving it with Dx and Dy.
                    </p>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
                        <Figure
                            src={"/proj2/cameraman_2step_dog_gaussian.jpg"}
                            caption={"Step 1: blur the image by convolving with a Gaussian filter"}
                            style_width="15vw"
                        />
                        <Figure
                            src={"/proj2/cameraman_2step_dog_dx.jpg"}
                            caption={"Step 2A: convolve the blurred image with Dx"}
                            style_width="15vw"
                        />
                        <Figure
                            src={"/proj2/cameraman_2step_dog_dy.jpg"}
                            caption={"Step 2B: convolve the blurred image with Dy"}
                            style_width="15vw"
                        />
                        <Figure
                            src={"/proj2/cameraman_2step_dog.jpg"}
                            caption={"Step 3: Compute the magnitude of the gradients and binarize edges"}
                            style_width="15vw"
                        />
                    </div>
                    <p>For each of Dx and Dy, this requires convolving the image with 2 separate filters (convolve with a Gaussian, then convolve again with either Dx or Dy).
                        Based on the derivative theorem of convolution, the same process can be implemented by convolving the image with a single filter: a derivative of a Gaussian (DoG).
                        To produce this filter, I first convolved a Gaussian filter with Dx and Dy respectively.
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="The derivative theorem of convolution"
                        dangerouslySetInnerHTML={{ __html: derivativeTheoremOfConvolutionRendered }}
                    />
                    <p>This is what taking the derivative of a 9x9 Gaussian looks like! AKA convolving the Gaussian kernel with the Dx kernel and the Dy kernel.
                    </p>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        <Figure
                            src={"/proj2/cameraman_gaussian_derivatives.jpg"}
                            caption={"Taking the derivative of a Gaussian by convolving the Gaussian kernel with Dx and Dy"}
                            style_width="50vw"
                        />
                    </div>
                    <p>And these are the results of convolving the same cameraman.jpg image with the single-step DoG filters for detecting vertical and horizontal edges, then calculating its gradient magintidue and binarizing edges.
                    </p>
                    <div className="grid grid-cols-1 items-center gap-4 md:grid-cols-3">
                        <Figure
                            src={"/proj2/cameraman_1step_dog_dx.jpg"}
                            caption={"Single-conv DoG filter to detect vertical edges"}
                            style_width="25vw"
                        />
                        <Figure
                            src={"/proj2/cameraman_1step_dog_dy.jpg"}
                            caption={"Single-conv DoG filter to detect horizontal edges"}
                            style_width="25vw"
                        />
                        <Figure
                            src={"/proj2/cameraman_1step_dog.jpg"}
                            caption={"Binarized edges from the single-conv DoG filters"}
                            style_width="25vw"
                        />
                    </div>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        <Figure
                            src={"/proj2/cameraman_dog_comparison.jpg"}
                            caption={"Comparing two-conv versus single-conv DoG filter results"}
                            style_width="50vw"
                        />
                    </div>
                </section>
                <section id="part_2.1_sharpening" className="space-y-5">
                    <h2 className="font-medium">Part 2.1: Image Sharpening</h2>
                    <p>Applying (convolving) a Gaussian kernel to an image produces a blurrier version of that image —
                        the Gaussian kernel acts as a low-pass filter such that the result only contains the low frequencies of the image.

                        Subtracting the blurred version from the original image gives us the image's high frequencies.

                        We can then add the high frequencies back to the original image (sometimes scaled by some ɑ to control the "sharpness") to make it look sharper!
                    </p>
                    <p>This sequence of operations — blur an image using a Gaussian kernel, subtract the blurred image from the original image to get the high frequencies, then
                        adding the high frequencies back to the original image to create a sharpened version — can be combined into a single convolution called the unsharp mask filter (AKA the sharpening filter).

                        In the following formula for the sharpening filter, f represents the original image, g represents the Gaussian kernel,
                        and e is the unit impulse (essentially an identity kernel whose response is the same input it is convolved with).
                        Alpha is a scalar value that determines how "sharp" the result looks.
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="A formula to calculate the output dimensions of a convolution"
                        dangerouslySetInnerHTML={{ __html: sharpeningFilterRendered }}
                    />
                    <div className="grid grid-cols-1 gap-x-4 gap-y-8 md:grid-cols-2 justify-items-center">
                        <Figure
                            src={"/proj2/taj.jpg"}
                            caption={"taj.jpg (original)"}
                            style_width="25vw"
                        />
                        <Figure
                            src={"/proj2/taj_sharpen_0.01.jpg"}
                            caption={`taj.jpg sharpened with a single-conv sharpening mask (${ALPHA_UNICODE} = 0.01)`}
                            style_width="25vw"
                        />
                        <Figure
                            src={"/proj2/taj_sharpen_0.1.jpg"}
                            caption={`taj.jpg sharpened with a single-conv sharpening mask (${ALPHA_UNICODE} = 0.1)`}
                            style_width="25vw"
                        />
                        <Figure
                            src={"/proj2/taj_sharpen_0.25.jpg"}
                            caption={`taj.jpg sharpened with a single-conv sharpening mask (${ALPHA_UNICODE} = 0.25)`}
                            style_width="25vw"
                        />
                        <Figure
                            src={"/proj2/taj_sharpen_0.5.jpg"}
                            caption={`taj.jpg sharpened with a single-conv sharpening mask (${ALPHA_UNICODE} = 0.5)`}
                            style_width="25vw"
                        />
                        <Figure
                            src={"/proj2/taj_sharpen_1.0.jpg"}
                            caption={`taj.jpg sharpened with a single-conv sharpening mask (${ALPHA_UNICODE} = 1.0)`}
                            style_width="25vw"
                        />
                        <Figure
                            src={"/proj2/taj_sharpen_2.0.jpg"}
                            caption={`taj.jpg sharpened with a single-conv sharpening mask (${ALPHA_UNICODE} = 2.0)`}
                            style_width="25vw"
                        />
                        <Figure
                            src={"/proj2/taj_sharpen_5.0.jpg"}
                            caption={`taj.jpg sharpened with a single-conv sharpening mask (${ALPHA_UNICODE} = 5.0)`}
                            style_width="25vw"
                        />
                    </div>
                    <p>Here are some additional images of my own that I tried sharpening!</p>
                    <div className="grid grid-cols-1 gap-x-4 gap-y-8 md:grid-cols-2 justify-items-center">
                        TODO
                    </div>
                    <p>As an additional experiment, I also tried picking a sharp image, blurring it, then re-sharpening it.

                        Blurring then re-sharpening didn't seem to recover the original image.
                        Blurring discards some of the fine details in the original image.
                        Applying the sharpening mask boosts the high-frequency details remaining in the blurred image,
                        but it can't recover the information that was lost.

                        Moreover, in the real world, rounding and numerical representation can make it impossible to reconstruct image data after it's been transformed.
                    </p>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        <Figure
                            src={"/proj2/taj_sharpen_blur_sharpen.jpg"}
                            caption={"Sharpening an image, blurring it, and then re-sharpening it again does not recover the original image or the sharpened image"}
                            style_width="50vw"
                        />
                    </div>
                </section>
                <section id="part_2.2_hybrid" className="space-y-5">
                    <h2 className="font-medium">Part 2.2: Hybrid Images</h2>
                </section>
                <section id="part_2.3_stacks" className="space-y-5">
                    <h2 className="font-medium">Part 2.3: Gaussian and Laplacian Stacks</h2>
                </section>
                <section id="part_2.4_blend" className="space-y-5">
                    <h2 className="font-medium">Part 2.4: Multiresolution Blending (AKA the oraple!)</h2>
                </section>
            </article>
            <aside className="fixed right-0 top-20 hidden h-fit max-h-[70vh] w-[15vw] min-w-[150px] px-4 overflow-y-auto border-l-2 border-gray-200 md:block">
                <TableOfContents contents={contents} />
            </aside>
        </main>
    );
}