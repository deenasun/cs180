"use client"

import katex from "katex";
import "katex/dist/katex.min.css";


export default function Equation({ rawString, ariaLabel }: { rawString: string, ariaLabel?: string }) {

    const rendered = katex.renderToString(rawString, {
        displayMode: true,
        throwOnError: false,
    });

    return (
        <div
            className="my-6 overflow-x-auto text-center"
            aria-label={ariaLabel}
            dangerouslySetInnerHTML={{ __html: rendered }}
        />
    )
}