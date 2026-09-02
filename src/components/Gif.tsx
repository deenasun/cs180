"use client";

import Image from "next/image";
import { getAssetPath } from "@/shared";
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
    const [tooltipPosition, setTooltipPosition] = useState({
        x: 0,
        y: 0,
    });

    function handleMouseMove(event: React.MouseEvent<HTMLAnchorElement>) {
        const bounds = event.currentTarget.getBoundingClientRect();

        setTooltipPosition({
            x: event.clientX - bounds.left + 12,
            y: event.clientY - bounds.top + 12,
        });
    }

    const previous = useCallback(() => {
        setIndex((current) => (current - 1 + imagePaths.length) % imagePaths.length);
    }, [imagePaths.length])

    const next = useCallback(() => {
        setIndex((current) => (current + 1) % imagePaths.length);
    }, [imagePaths.length])

    useEffect(() => {
        if (!playing) return;

        const timer = setInterval(next, 200);

        return () => clearInterval(timer);
    }, [playing, next])

    return (
        <div className="flex flex-col items-center justify-center w-[25vw]">
            {/* Image with overlayed text */}
            <div className="relative inline-block">
                <a href={getAssetPath("/proj0/dolly_zoom/sather_gate_dolly_zoom.gif")}
                    download="sather_gate_dolly_zoom.gif"
                    onMouseMove={handleMouseMove}
                    className="group relative block cursor-pointer"
                >
                    <span
                        style={{
                            left: tooltipPosition.x,
                            top: tooltipPosition.y,
                        }}
                        className="pointer-events-none absolute z-10
                            whitespace-nowrap
                            rounded-md bg-space-black/60
                            px-2 py-1
                            text-xs text-cream
                            opacity-0 transition-opacity group-hover:opacity-100"
                    >
                        Click to download GIF
                    </span>
                    <Image
                        src={getAssetPath(imagePaths[index])}
                        alt={`Image ${index + 1} of ${imagePaths.length}`}
                        width={1440}
                        height={1080}
                        style={{ width: "full", height: 'auto' }}
                        className="rounded-md"
                    />
                </a>
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
