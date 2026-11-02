"use client";

/* The same Galaxy component as used in deenasun.github.io */

import { useRef, useEffect, useState } from "react";
import * as THREE from "three";
import { initStars } from "@/components/SpaceObjects";

export default function Galaxy({
	width = 400,
	height = 300,
}: {
	width?: number;
	height?: number;
}) {
	const canvasRef = useRef<HTMLCanvasElement | null>(null);
	const containerRef = useRef<HTMLDivElement | null>(null);
	const sceneRef = useRef<THREE.Scene | null>(null);
	const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
	const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
	const [dimensions, setDimensions] = useState({ width, height });

	// handle container resize safely
	useEffect(() => {
		const updateDimensions = () => {
			if (containerRef.current) {
				const rect = containerRef.current.getBoundingClientRect();
				setDimensions({
					width: rect.width,
					height: rect.height,
				});
			}
		};

		// set initial dimensions
		updateDimensions();

		// add event listener for window resize
		window.addEventListener("resize", updateDimensions);

		// cleanup
		return () => window.removeEventListener("resize", updateDimensions);
	}, []);

	useEffect(() => {
		if (!canvasRef.current) return;

		// store ref in variable to avoid cleanup issues
		const canvas = canvasRef.current;

		// scene setup
		const scene = new THREE.Scene();
		sceneRef.current = scene;

		// camera setup
		const camera = new THREE.PerspectiveCamera(
			75,
			dimensions.width / dimensions.height,
			0.1,
			1000
		);

		camera.position.set(0, 20, 50);
		camera.lookAt(0, 0, 0);
		cameraRef.current = camera;

		// renderer setup
		const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
		renderer.setSize(dimensions.width, dimensions.height);
		if (typeof window !== "undefined") {
			renderer.setPixelRatio(window.devicePixelRatio);
		}
		renderer.setClearColor(0x000000, 0); // transparent background
		rendererRef.current = renderer;
		// create stars object
		const stars = initStars();
		stars.name = "stars";
		scene.add(stars);

		// animation
		function animate() {
			stars.rotation.y += 0.0001; // rotate the stars around the y-axis
			renderer.render(scene, camera);
		}
		renderer.setAnimationLoop(animate); // calls animate function 60 times per second

		// cleanup
		return () => {
			// Stop animation and dispose Three.js entities to release resources
			renderer.setAnimationLoop(null);
			stars.geometry.dispose();
			stars.material.dispose();
			renderer.dispose();
		};
	}, [dimensions.width, dimensions.height]);

	return (
		<div
			ref={containerRef}
			className="inset-0 fixed z-0 pointer-events-none"
			style={{ width: "100%", height: "100%" }}
		>
			<canvas
				ref={canvasRef}
				className="w-full h-full"
				style={{ width: "100%", height: "100%" }}
			/>
		</div>
	);
}
