"use client";

type ContentItem = {
    sectionLink: string;
    text: string;
}

export default function TableOfContents({ contents }: { contents: ContentItem[] }) {
    return (
        <>
            <h2 className="text-sm font-bold text-gray-900">Contents</h2>
            <nav className="mt-4">
                <ul className="space-y-3 text-sm">
                    {
                        contents.map((item, index) => (
                            <li key={item.sectionLink}>
                                <a href={`#${item.sectionLink}`} className="text-gray-600 hover:text-gray-900">
                                    {item.text}
                                </a>
                            </li>
                        ))
                    }
                </ul>
            </nav>
        </>
    )
}