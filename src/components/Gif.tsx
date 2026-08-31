"use client";

import Image from "next/image";
import { useCallback, useEffect, useState } from "react";

type GifButtonProps = {
    onClick: () => void;
    disabled?: boolean;
    text: string;
}

const GifButton = ({
    onClick,
    disabled = false,
    text
}: GifButtonProps) => {
    return (
        <button
            type="button"
            onClick={onClick}
            disabled={disabled}
            className="w-[12vh] min-w-[120px]
                whitespace-pre-line
                p-1
                rounded-md
                border-2 border-gray-200
                enabled:hover:bg-gray-100 enabled:hover:cursor-pointer
                disabled:cursor-not-allowed">
            {text}
        </button>
    )
}


export default function Gif({
    imagePaths
}: { imagePaths: string[] }) {
    const [index, setIndex] = useState(0);
    const [playing, setPlaying] = useState(true);

    const previous = useCallback(() => {
        setIndex((current) => (current - 1 + imagePaths.length) % imagePaths.length);
    }, [])

    const next = useCallback(() => {
        setIndex((current) => (current + 1) % imagePaths.length);
    }, [])

    useEffect(() => {
        if (!playing) return;

        const timer = setInterval(next, 200);

        return () => clearInterval(timer);
    }, [playing, next])

    return (
        <div>
            {/* Image with overlayed text */}
            <div className="relative inline-block">
                <Image
                    src={imagePaths[index]}
                    alt={`Image ${index + 1} of ${imagePaths.length}`}
                    width={400}
                    height={400}
                    style={{ width: "60vh", height: 'auto' }}
                    className="rounded-md"
                />
                <div className="pointer-events-none absolute bottom-2 right-2 rounded-md bg-space-black/60 px-2 py-1 text-sm text-cream">{index + 1}/{imagePaths.length}</div>
            </div>
            <div className="mt-2 flex flex-row gap-2 justify-between">
                <GifButton onClick={previous} disabled={playing} text="Previous" />
                <GifButton onClick={() => setPlaying((playingValue => !playingValue))} text={playing ? "Pause" : "Autoplay"} />
                <GifButton onClick={next} disabled={playing} text="Next" />
            </div>
        </div >
    )
}