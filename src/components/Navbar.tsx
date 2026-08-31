"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
    const pathname = usePathname();

    const projects = [
        {
            path: "/proj0",
            name: "Project 0"
        },
        {
            path: "/proj1",
            name: "Project 1"
        },
        {
            path: "/proj2",
            name: "Project 2"
        },
        {
            path: "/proj3",
            name: "Project 3"
        },
        {
            path: "/proj4",
            name: "Project 4"
        },
        {
            path: "/final_proj",
            name: "Final Project"
        },
    ]

    return (
        <nav className="bg-white/80 flex flex-row justify-between items-center h-16 border-b-2 border-gray-200 sticky top-0 z-50 px-4 sm:px-8">
            <div className="flex-shrink-0">
                <h1>Deena&apos;s CS 180 Portfolio</h1>
            </div>
            <div className="links flex items-center justify-end gap-x-8 ml-auto">
                {projects.map((proj) =>
                    pathname == proj.path ?
                        (
                            <p
                                key={proj.name}
                                className="text-gray-600 px-3 py-2 rounded-md text-sm font-medium cursor-default underline underline-offset-4"
                            >
                                {proj.name}
                            </p>
                        ) : (
                            <Link
                                href={proj.path}
                                key={proj.name}
                                className={`text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium transition-colors`}
                            >
                                {proj.name}
                            </Link>

                        )
                )}
            </div>
        </nav>
    )
}
