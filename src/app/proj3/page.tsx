import katex from "katex";
import "katex/dist/katex.min.css";

import Figure from "@/components/Figure";
import TableOfContents from "@/components/TableOfContents";

export default function Page() {
    const contents = [
        {
            sectionLink: "part_a_1",
            text: "Part A: Visualizing Training and Sampling"
        },
        {
            sectionLink: "part_a_2",
            text: "Part A: Conditional Generation and Guidance"
        },
        {
            sectionLink: "part_a_3",
            text: "Part A: Creative Applications"
        },
        {
            sectionLink: "part_b",
            text: "Part B"
        },
    ]

    const linearInterpolation = String.raw`x_t = (1 - t) \cdot x_0 + t \cdot x_1 \\ \quad t \in [0, 1], \quad x_0 = \epsilon \sim N(0, I)`

    const linearInterpolationRendered = katex.renderToString(linearInterpolation, {
        displayMode: true,
        throwOnError: false,
    });

    const oneStepDenoising = String.raw`\hat{x_1} = x_t + (1 - t) \cdot v_{\theta}(x_t, t, c)`

    const oneStepDenoisingRendered = katex.renderToString(oneStepDenoising, {
        displayMode: true,
        throwOnError: false,
    });

    return (
        <main className="mx-4 my-2 sm:mx-8">
            <article className="mr-[17vw] space-y-12">
                <h1 className="font-bold">Project 3: Fun with Flow Models</h1>
                <div className="flex flex-row w-full justify-center space-x-20">
                    <Figure
                        src={"/proj3/part_a/proj3_1-1.jpg"}
                        caption={"A noisy cat in Santorini, Greece"}
                        style_width="50vw"
                        loading="eager"
                    />
                </div>
                <section id="part_a_1" className="space-y-5">
                    <h2 className="font-medium">Visualizing Training and Sampling</h2>
                    <p>The optimal-transport formulation of flow matching uses linear interpolation to construct an intermediate image xt in between the clean image x1 and an image of pure Gaussian noise x0.
                        t = 0 corresponds to pure noise, and t = 1 corresponds to a clean image.
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="Linear interpolation for flow matching"
                        dangerouslySetInnerHTML={{ __html: linearInterpolationRendered }}
                    />
                    <h3 className="font-medium">1.1 Constructing Noisy Training Inputs</h3>
                    <p>First, I sampled a tensor with shape (H, W, 3) from a Guassian distribution.
                        Then, I computed a weighted sum of the original image and the noisy image at t = [0.25, 0.50, and 0.75].
                        The bigger the t, the more of the original image information is retained!</p>
                    <div className="flex flex-row w-full justify-center space-x-20">
                        <Figure
                            src={"/proj3/part_a/proj3_1-1.jpg"}
                            caption={"The original santorini_cat.jpg image and interpolations at t = [0.25, 0.50, 0.75]"}
                            style_width="50vw"
                        />
                    </div>
                    <h3 className="font-medium">1.2 Classical Denoising</h3>
                    <p>
                        Applying a Gaussian blur to an image essentially averages neighboring pixels.
                        A strong blur reduces noise but also removes image detail.
                        In this part, I applied Gaussian blurs (with sigma scaled based on t) to reconstruct the original image.
                        This provides a helpful baseline to compare with learned flow models later on!
                    </p>
                    <p>
                        Below, you can view each of the 3 noisy versions of santorini_cat.jpg side-by-side with a Gaussian-denoised version.
                    </p>
                    <div className="flex flex-col w-full justify-center items-center space-y-4">
                        <Figure
                            src={"/proj3/part_a/proj3_1-2_025.jpg"}
                            caption={"Noisy image at t = 0.25 and Gaussian denoising with sigma = 8.0"}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_1-2_050.jpg"}
                            caption={"Noisy image at t = 0.50 and Gaussian denoising with sigma = 4.0"}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_1-2_075.jpg"}
                            caption={"Noisy image at t = 0.75 and Gaussian denoising with sigma = 2.0"}
                            style_width="50vw"
                        />
                    </div>
                    <h3 className="font-medium">1.3 One-Step Denoising</h3>
                    <p>
                        Next, I used a pretrained flow model <a href="https://huggingface.co/MCG-NJU/PixNerd-XXL-P16-T2I" target="_blank" rel="noopener noreferrer" className="text-[var(--color-code-blue)] hover:underline">PixNerd-XXL-P16-T2I</a>
                        to predict the velocity given a noisy image and the timestep.

                        Since PixNerd was trained with text-conditioning, so I used the placeholder "a high quality photo" as the text input for now.

                        I implemented one-step denoising by extraploating directly to the clean endpoint with this single, predicted velocity:
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="Linear interpolation for flow matching"
                        dangerouslySetInnerHTML={{ __html: oneStepDenoisingRendered }}
                    />
                    <p>
                        These are the results of one-step denoising! The leftmost image is the original, the middle image is the noisy interpolation, and the rightmost image is the predicted clean image using one-step denoising.
                    </p>
                    <div className="flex flex-col w-full justify-center items-center space-y-4">
                        <Figure
                            src={"/proj3/part_a/proj3_1-3_025.jpg"}
                            caption={"Noisy image at t = 0.25 and an estimate of the original image with one-step denoising"}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_1-3_050.jpg"}
                            caption={"Noisy image at t = 0.50 and an estimate of the original image with one-step denoising"}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_1-3_075.jpg"}
                            caption={"Noisy image at t = 0.75 and an estimate of the original image with one-step denoising"}
                            style_width="50vw"
                        />
                    </div>
                </section>
            </article>
            <aside className="fixed right-0 top-20 hidden h-fit max-h-[70vh] w-[15vw] min-w-[150px] px-4 overflow-y-auto border-l-2 border-gray-200 md:block">
                <TableOfContents contents={contents} />
            </aside>
        </main>
    );
}