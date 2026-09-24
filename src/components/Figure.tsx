"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { getAssetPath } from "@/shared"


export default function Figure({
    src,
    caption,
    subcaption,
    style_width,
    style_height,
    loading
}: {
    src: string,
    caption: string,
    subcaption?: string | null
    style_width?: string | null,
    style_height?: string | null,
    loading?: "eager" | "lazy";
}) {
    // Focus on the figure if mouse hovers and stays over the image
    const [isHovering, setIsHovering] = useState(false);
    const [isFocused, setIsFocused] = useState(false);
    const hoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

    const handleMouseEnter = () => {
        setIsHovering(true);

        hoverTimer.current = setTimeout(() => {
            setIsFocused(true);
        }, 1000);
    };

    const handleMouseLeave = () => {
        setIsHovering(false);

        if (hoverTimer.current) {
            clearTimeout(hoverTimer.current);
        }
    };

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                setIsFocused(false);
            }
        };

        window.addEventListener("keydown", handleKeyDown);

        return () => {
            window.removeEventListener("keydown", handleKeyDown);

            if (hoverTimer.current) {
                clearTimeout(hoverTimer.current);
            }
        };
    }, []);

    return (
        <>
            <figure
                className={`flex w-full max-w-2xl flex-col items-center ${style_width ? "" : "mx-auto"}`}
                style={style_width ? { width: style_width } : undefined}
            >
                <div
                    className="relative cursor-zoom-in items-center"
                    onMouseEnter={handleMouseEnter}
                    onMouseLeave={handleMouseLeave}
                >
                    <Image
                        key={src}
                        src={getAssetPath(src)}
                        alt={caption}
                        height={1080}
                        width={1080}
                        loading={loading}
                        style={{
                            width: style_width ?? "auto",
                            height: style_width ? "auto" : (style_height ?? "40vh"),
                        }}
                    />
                    {isHovering && (
                        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex items-center justify-center gap-2 rounded bg-space-black/80 px-3 py-1 text-sm text-cream">
                            <span className="text-center">Hover to zoom</span>
                            <span className="h-3 w-3 shrink-0 animate-spin rounded-full border-2 border-cream border-t-transparent" />
                        </div>
                    )}
                </div>
                <figcaption className="mt-2 text-center text-sm text-gray-600">
                    {caption}
                </figcaption>
                {subcaption != null && (
                    <figcaption className="mt-2 text-center text-xs text-gray-600">
                        {subcaption}
                    </figcaption>
                )}
            </figure>
            {/* Smooth transition for the focus overlay */}
            <div
                className={`fixed inset-0 z-50 flex items-center justify-center bg-space-black/80 p-8
        transition-opacity duration-300 ease-out
        ${isFocused
                        ? "pointer-events-auto opacity-100"
                        : "pointer-events-none opacity-0"
                    }`}
                onClick={() => setIsFocused(false)}
            >
                <Image
                    src={getAssetPath(src)}
                    alt={caption}
                    width={2000}
                    height={2000}
                    className={`max-h-full max-w-full object-contain
            transition-transform duration-300 ease-out`}
                />
            </div>
        </>

    )
}
