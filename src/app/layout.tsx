import type { Metadata } from "next";
import { Roboto_Mono } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";
import Navbar from "@/components/Navbar";

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
            <body className={robotoMono.variable} style={{marginBottom: "1.5rem"}}>
                <Navbar />
                {children}
            </body>
        </html>
    );
}