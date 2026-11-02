import type { Metadata } from "next";
import { Roboto_Mono } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Galaxy from "@/components/Galaxy";

const robotoMono = Roboto_Mono({
    variable: "--font-roboto-mono",
    subsets: ["latin"],
});

export const metadata: Metadata = {
    title: "Deena's CS 180 Portfolio",
    description: "Deena's CS 180 Portfolio",
};

export default function RootLayout({
    children,
}: {
    children: ReactNode;
}) {
    return (
        <html lang="en">
            <body className={robotoMono.variable}>
                <Galaxy />
                <div className="relative z-10">
                    <Navbar />
                    {children}
                </div>
            </body>
        </html>
    );
}