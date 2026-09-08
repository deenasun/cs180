import TableOfContents from "@/components/TableOfContents";

export default function Page() {
    const contents = [
        {
            sectionLink: "context",
            text: "Background Context"
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
    return (
        <main className="mx-4 my-2 sm:mx-8">
            <article className="mr-[17vw] max-w-4xl space-y-12">
                <h1>Project 1: Colorizing the Prokudin-Gorskii Photo Collection</h1>

                <section id="context">Background Context</section>
                <section id="basic_alignment">Single-Scale Alignment</section>
                <section id="image_pyramids">Image Pyramids</section>
                <section id="bells_and_whistles">Bells and Whistles!</section>
            </article>

            <aside className="fixed right-0 top-20 hidden h-fit max-h-[70vh] w-[15vw] min-w-[150px] px-4 overflow-y-auto border-l-2 border-gray-200 md:block">
                <TableOfContents contents={contents} />
            </aside>
        </main>
    );
}