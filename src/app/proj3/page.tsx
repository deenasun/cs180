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

    const linearInterpolation = String.raw`x_t = (1 - t) \cdot x_0 + t \cdot x_1 \quad t \in [0, 1], \quad x_0 = \epsilon \sim N(0, I)`

    const linearInterpolationRendered = katex.renderToString(linearInterpolation, {
        displayMode: true,
        throwOnError: false,
    });

    const oneStepDenoising = String.raw`\hat{x_1} = x_t + (1 - t) \cdot v_{\theta}(x_t, t, c)`

    const oneStepDenoisingRendered = katex.renderToString(oneStepDenoising, {
        displayMode: true,
        throwOnError: false,
    });

    const multiStepDenoising = String.raw`x_{t + \Delta t} = x_t + \Delta t \cdot v_{\theta}(x_t, t, c)`

    const multiStepDenoisingRendered = katex.renderToString(multiStepDenoising, {
        displayMode: true,
        throwOnError: false,
    });

    const cfgEquation = String.raw`\begin{aligned}
v_{cfg} = v_c + w \cdot (v_c - v_u) \\
x_{t + \Delta t} = x_t + \Delta t \cdot v_{cfg}
\end{aligned}`

    const cfgEquationRendered = katex.renderToString(cfgEquation, {
        displayMode: true,
        throwOnError: false,
    });

    const visualAnagramEquation = String.raw`
    \begin{gathered}
    v_1 = \operatorname{CFG\ velocity}(x_t, t, p_1) \\
    v_2 = \operatorname{flip}(\operatorname{CFG\ velocity}(\operatorname{flip}(x_t), t, p_2)) \\
    v = \frac{v_1 + v_2}{2}
    \end{gathered}
    `;

    const visualAnagramEquationRendered = katex.renderToString(visualAnagramEquation, {
        displayMode: true,
        throwOnError: false,
    });

    const hybridImagesEquation = String.raw`
    \begin{gathered}
    v_1 = \operatorname{CFG\ velocity}(x_t, t, p_1) \\
    v_2 = \operatorname{CFG\ velocity}(x_t, t, p_2) \\
    v = f_{lowpass}(v1) + f_{highpass}
    \end{gathered}
    `;

    const hybridImagesEquationRendered = katex.renderToString(hybridImagesEquation, {
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
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
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
                        {"\n\n"}
                        Since PixNerd was trained with text-conditioning, so I used the placeholder "a high quality photo" as the text input for now.
                        {"\n\n"}
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
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
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
                    <h3 className="font-medium">1.4 Visualizing Velocity</h3>
                    <p>
                        For each time t = 0.25, 0.50, 0.75, I visualized the noisy image x_t, the predicted one-step update (1 - t) v, and the ground truth update x_1 - x_t.
                        I also included an error heatmap based on the root-mean-square difference between predicted update and the ground-truth update. First, I squared the differences
                        at each pixel in each color channels, averaged the squared differences across the RGB channels, then took the square root. This results in one error value per pixel position.
                    </p>
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
                        <Figure
                            src={"/proj3/part_a/santorini_cat.jpg"}
                            caption={"The original santorini_cat.jpg image."}
                            style_width="20vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_1-4_025.jpg"}
                            caption={"Visualizing velocities and RGB RMS error at t = 0.25."}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_1-4_050.jpg"}
                            caption={"Visualizing velocities and RGB RMS error at t = 0.50."}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_1-4_075.jpg"}
                            caption={"Visualizing velocities and RGB RMS error at t = 0.75."}
                            style_width="50vw"
                        />
                    </div>
                    <h3 className="font-medium">1.5 Iterative Denoising with Euler Sampling</h3>
                    <p>
                        Rather than denoising the image from x_0 (pure noise) to x_1 (clean image) in a single step, we can use multi-step sampling.
                        I implemented Euler integration by dividing the time from [0, 1] into small step sizes. At each timestep, I used the flow-matching model to predict the velocity at the current timestep,
                        then took a small step in the direction of the predicted veolocity.
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="Euler integration for multi-step denoising"
                        dangerouslySetInnerHTML={{ __html: multiStepDenoisingRendered }}
                    />
                    <p>
                        Here are the results of starting with a noisy version of santorini_cat.jpg at t = 0.50, and taking 25 Euler integration steps.
                    </p>
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
                        <Figure
                            src={"/proj3/part_a/proj3_1-5.jpg"}
                            caption={"25 denoising steps, starting from t = 0.50"}
                            style_width="50vw"
                        />
                    </div>
                    <p>
                        Comparing the results of multi-step denoising with one-step denoising, Gaussian blur, and the original image (the ground truth!).
                        Out of the 3 denoising methods so far, multi-step denoising recovers the original image the best.
                        In multi-step denoising, at every step the model can base its prediction of the velocity on a less noisy input x_t; therefore
                        every step the algorithm takes can "self-adjust" to more closely follow the true flow path.
                    </p>
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
                        TODO
                    </div>
                    <h3 className="font-medium">1.6 Generating Images from Noise</h3>
                    <p>
                        By passing in pure noise (x_0) and t = 0 to the multi-step denoising algorithm, we can generate images from scratch!
                        {"\n\n"}
                        Here are 5 results of denoising pure noise, with the prompt "a high quality photo".
                        All 5 results were of human-like subjects (quite uncanny valley). It seems that PixNerd favors human subjects when given this generic prompt!
                    </p>
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
                        <Figure
                            src={"/proj3/part_a/proj3_1-6.jpg"}
                            caption={"Generating 5 images by starting with pure noise initialized with different seeds."}
                            style_width="50vw"
                        />
                    </div>
                </section>
                <section id="part_a_2" className="space-y-5">
                    <h2 className="font-medium">Conditional Generation and Guidance</h2>
                    <h3 className="font-medium">2.1 Classifier-Free Guidance (CFG)</h3>
                    <p>
                        Conditional guidance is when a model generates an image based on a certain condition, such as a provided text prompt.
                        In classifier-free guidance (CFG), the flow-matching model is trained to denoise images with a condition, and without any condition (e.g. with a "null" or empty-string as the condition).
                        Then, during each step of sampling, we run a forward pass through the model with the condition to produce a conditional velocity v_c, and another forward pass through
                        the same model without any condition to produce an unconditional velocity v_u.
                        Subtracting v_c - v_u gives us a vector that points from the unconditional flow to the conditional flow (i.e. a direction pointing towards the class/condition).
                        Adding this vector to the conditional velocity (with a scalar weight to control how much we wish to "exaggerate" the guidance) results in a velocity
                        that is guided towards the desired condition.
                        {"\n\n"}
                        Setting w greater than 1 pushes the flow-matching model to generate features or images that emphasize what make the given condition distinct.
                        {"\n\n"}
                        This algorithm is called "classifier-free" because it doesn't involve training a separate classifier to score whether or not the model produces the relevant image for the given condition.
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="Classifier-free guidance"
                        dangerouslySetInnerHTML={{ __html: cfgEquationRendered }}
                    />
                    <p>
                        Here are the results of generating images from pure-noise using the same text prompt "a high quality photo" as in part 1.6, but now implemented with CFG with w=7.
                        Using CFG, the images are still of human subjects but look much more realistic. Using a high value for w helped push the generated images closer towards realistic subjects.
                    </p>
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
                        <Figure
                            src={"/proj3/part_a/proj3_2-1.jpg"}
                            caption={"Generating 5 images with the text prompt \"a high quality photo\" via classifier-free guidance (w=7)."}
                            style_width="50vw"
                        />
                    </div>
                </section>
                <section id="part_a_3" className="space-y-5">
                    <h2 className="font-medium">Creative Applications</h2>
                    <h3 className="font-medium">3.1 Image-to-Image Editing</h3>
                    <p>
                        Denoising also allows us to "edit" pictures! In order to denoise an image, the flow model has to be "creative" in order to
                        guide the noisy image back onto thee manifold of natural images.
                        {"\n\n"}
                        If we take an image, add some noise to it, then run multi-step denoising from a partially noisy image, we can get a result that is similar to the original image
                        but with some creative, artistic edits!
                        {"\n\n"}
                        Below, I ran the forward, noise-adding process to an image of the Campanile to get a noisy image at various times: t = [0.02, 0.04, 0.06, 0.10, 0.14, 0.25, 0.5].
                        Then, I ran the denoising process starting from these timestamps (again, with the generic text prompt "a high quality photo" passed to the PixNerd flow model)
                        to "edit" the pictures. The later the starting time, the more of the original image's information is retained in
                        the partially noisy image the denoising process starts from, and the closer the final result is to the original clean image.
                        {"\n\n"}
                        I also tried editing 2 of my own images: a picture of a cat I took on Santorini island, Greece and a picture of a windmill I took in the Netherlands.
                    </p>
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
                        <Figure
                            src={"/proj3/part_a/proj3_3-1_campanile.jpg"}
                            caption={"The results of editing campanile.jpg starting at various intial times. Earlier starting times starting denoising from almost pure noise and resulted in very different final images than the original campanile.jpg."}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_3-1_santorini_cat.jpg"}
                            caption={"The results of editing a cat on the Greek island of Santorini starting at various intial times."}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_3-1_windmill.jpg"}
                            caption={"The results of editing an image of a windmill from the Netherlands starting at various intial times."}
                            style_width="50vw"
                        />
                    </div>
                    <h3 className="font-medium">Editing Hand-Drawn and Web Images</h3>
                    <p>
                        Editing via denoising can produce some fun results if we start out with a non-realistic image, like drawings or pixel art, then try to denoise it back onto the natural image manifold.
                        {"\n\n"}
                        Here are the results of editing-via-denoising on a web image of the Golden Gate Bridge, and on two hand-drawn images.
                        I tried editing starting from 7 different times t = [0.02, 0.04, 0.06, 0.10, 0.14, 0.25, 0.5].
                    </p>
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
                        TODO
                    </div>
                    <h3 className="font-medium">3.2 Text-Guided Image Editing</h3>
                    <p>
                        Next, I tried editing via denoising with a prompt describing the edit procedure.
                        {"\n\n"}
                        The text-guided image editing results more closely reflected the text prompt when starting from early time steps like t = 0.02, t = 0.04, or t = 0.06.
                        When the editing/denoising process began from later times, the flow model was not able to edit away from the original image information
                        still kept in the partially noisy starting image.
                        {"\n\n"}
                        So starting the editing process earlier on (where the initial input is closer to pure noise) generates a final results that favors the text prompt, whereas
                        starting the editing process later (where the initial input still retains a lot of the original image's information) generates a final result that is mostly the clean image.
                    </p>
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
                        <Figure
                            src={"/proj3/part_a/proj3_3-2_campanile_redwood.jpg"}
                            caption={"Editing campanile.jpg with the text prompt \"a redwod tree\""}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_3-2_santorini_cat_dragon.jpg"}
                            caption={"Editing santorini_cat.jpg with the text prompt \"a dragon sitting on top of a pile of treasure\""}
                            style_width="50vw"
                        />
                        <Figure
                            src={"/proj3/part_a/proj3_3-2_windmill_icecream.jpg"}
                            caption={"Editing windmill.jpg with the text prompt \"an ice cream sundae\""}
                            style_width="50vw"
                        />
                    </div>
                    <h3 className="font-medium">3.3 Visual Anagrams</h3>
                    <p>
                        Visual anagrams are images that look like one thing when right-side up, but look like another thing when flipped upside down!
                        {"\n\n"}
                        At every time step, I denoised the current x_t normally with prompt p_1 to produce a velocity estimate v_1.
                        Next, I rotated the current x_t by 180 degrees, denoised it with the second prompt p_2, and obtained a velocity estimate v_2.
                        Then, I flipped v_2 back around (since the model produces a velocity estimate for an image, the v_2 has the same dimensions as the image),
                        and averaged the two velocity estimates. Finally, I performed an Euler step with the average of the two velocities.
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="Linear interpolation for flow matching"
                        dangerouslySetInnerHTML={{ __html: visualAnagramEquationRendered }}
                    />
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
                        TODO
                    </div>
                    <h3 className="font-medium">3.4 Hybrid Images</h3>
                    <p>
                        Hybrid images are images that appear to depict different subjects when viewed up close and from far away.
                        They take advantage of how our eyes tend to perceive large features (i.e. low frequencies) when viewing something from far away,
                        but are more sensitive to fine details and edges (i.e. high frequencies) when viewing things from up close.
                        {"\n\n\n"}
                        To create hybrid images with flow models, at every denoising timestep t, I used the flow model to predict two velocities given the same x_t but different prompts.
                        Then, I combined the low frequencies of one velocity estimate with the high frequencies of another velocity estimate.
                        {"\n\n\n"}
                        A low-pass filter invovles convolving the velocity estimate with a Gaussian kernel.
                        The high-pass filter is the predition, minus a low-pass version of itself.
                    </p>
                    <div
                        className="my-6 overflow-x-auto text-center"
                        aria-label="Linear interpolation for flow matching"
                        dangerouslySetInnerHTML={{ __html: hybridImagesEquationRendered }}
                    />
                    <div className="flex flex-col w-full justify-center items-center space-y-8">
                        TODO
                    </div>

                </section>
            </article>
            <aside className="fixed right-0 top-20 hidden h-fit max-h-[70vh] w-[15vw] min-w-[150px] px-4 overflow-y-auto border-l-2 border-gray-200 md:block">
                <TableOfContents contents={contents} />
            </aside>
        </main>
    );
}
