import * as THREE from "three";

// Create a texture loader instance
const textureLoader = new THREE.TextureLoader();

function initSunCore(radius: number = 4) {
	const sunGeometry = new THREE.SphereGeometry(radius, 32, 32);
	const sunMaterial = new THREE.MeshBasicMaterial({ color: 0xffcc66 });
	const sun = new THREE.Mesh(sunGeometry, sunMaterial);
	return sun;
}

function initCorona(radius: number = 5) {
	const coronaGeometry = new THREE.SphereGeometry(radius, 32, 32);
	const positionAttribute = coronaGeometry.getAttribute("position"); // gets the position attribute of the geometry
	const originalPositions: [number, number, number][] = []; // stores original x, y, z coordinates of each vertex
	const randomOffsets: number[] = []; // stores a random "spikiness" for each vertex
	for (let i = 0; i < positionAttribute.count; i++) {
		// iterates through all the vertices
		const x = positionAttribute.getX(i);
		const y = positionAttribute.getY(i);
		const z = positionAttribute.getZ(i);
		originalPositions.push([x, y, z]);
		randomOffsets.push(Math.random() * 0.7 + 0.3); // each vertex gets a random "spikiness"
	}
	const coronaMaterial = new THREE.MeshBasicMaterial({
		color: 0xffee88,
		transparent: true,
		opacity: 0.5,
		side: THREE.DoubleSide,
	});
	const corona = new THREE.Mesh(coronaGeometry, coronaMaterial);

	// create a custom bounding box for the corona
	corona.geometry.computeBoundingBox();
	const bbox = corona.geometry.boundingBox!.clone();
	const expandBy = bbox.getSize(new THREE.Vector3()).multiplyScalar(0.05); // 5% bigger in each direction
	bbox.expandByVector(expandBy);
	corona.geometry.boundingBox = bbox;

	const animateCorona = (t: number) => {
		for (let i = 0; i < positionAttribute.count; i++) {
			// iterates through all the vertices
			const [x, y, z] = originalPositions[i];
			const scale = 1 + 0.15 * Math.sin(t * 2 + i) * randomOffsets[i]; // calculates the scale of the vertex
			positionAttribute.setXYZ(i, x * scale, y * scale, z * scale); // sets the new position of the vertex
		}
		positionAttribute.needsUpdate = true; // tells Three.js to update the position attribute of the geometry
	};
	return { corona, animateCorona };
}

function initSunGroup(sunRadius: number = 4, coronaRadius: number = 5) {
	const sunGroup = new THREE.Group();
	const sunCore = initSunCore(sunRadius);
	const { corona, animateCorona } = initCorona(coronaRadius);
	sunGroup.add(sunCore);
	sunGroup.add(corona);
	sunGroup.name = "sunGroup";
	sunCore.name = "sun";
	corona.name = "corona";
	return { sunGroup, animateCorona };
}

function initStars(numStars: number = 1000) {
	const geometry = new THREE.BufferGeometry();
	const positions = new Float32Array(numStars * 3); // 3 coordinates per star

	// generate random star positions in a sphere
	for (let i = 0; i < numStars * 3; i += 3) {
		// calculate spherical coordinates for star i
		const radius = Math.random() * 200 + 50; // star positions will be in a radius of 50-250
		const theta = Math.random() * Math.PI * 2; // star i will be located at longitude angle theta
		const phi = Math.acos(2 * Math.random() - 1); // star i will be located at latitude angle phi

		positions[i] = radius * Math.sin(phi) * Math.cos(theta); // x coordinate = radius * cos(theta) * sin(phi)
		positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta); // y coordinate = radius * sin(theta) * sin(phi)
		positions[i + 2] = radius * Math.cos(phi); // z coordinate = radius * cos(phi)
	}

	// set positions of the stars in the star bufferGeometry
	geometry.setAttribute(
		"position",
		new THREE.BufferAttribute(positions, 3) // tells bufferGeometry to read 3 values per star
	);

	// create star material (white points)
	const starMaterial = new THREE.PointsMaterial({
		color: 0xffffff,
		size: 1,
		transparent: true,
		opacity: 0.8,
	});

	const stars = new THREE.Points(geometry, starMaterial);
	return stars;
}

function initPlanet(
	name: string,
	radius: number = 10,
	color: number = 0x33568Cff,
	texturePath: string | null = null,
	hasRings: boolean = false,
	ringColor: number | null = null,
	rotationSpeed: number = 0.01,
	rotatesClockwise: boolean = true,
	angularVelocity: number = 0.001, // angular velocity in radians per frame
	orbitRadius: number = 20, // radius of the orbit
	axisTilt: number = 0 // tilt in radians (0 = no tilt, Math.PI/6 = 30 degrees, etc.)
) {
	// create a group for the planet and its rings
	const planetGroup = new THREE.Group();

	// create a planet
	const planetGeometry = new THREE.SphereGeometry(radius, 32, 32);
	// load texture if provided, otherwise use solid color
	let planetMaterial;
	if (texturePath) {
		const texture = textureLoader.load(texturePath);
		texture.flipY = false; // to prevent WebGL errors
		planetMaterial = new THREE.MeshBasicMaterial({
			map: texture,
		});
	} else {
		planetMaterial = new THREE.MeshBasicMaterial({
			color: color,
		});
	}
	const planet = new THREE.Mesh(planetGeometry, planetMaterial);
	// apply axis tilt to the planet
	planet.rotation.x = axisTilt; // positive x tilt = planet is tilted towards the viewer
	planet.rotation.z = Math.PI; // flip the planet 180 degrees to correct upside-down texture

	planetGroup.add(planet);

	if (hasRings && ringColor !== null) {
		// create a ring
		const innerRadius = radius * 1.1;
		const outerRadius = innerRadius * 1.5;

		const ringGeometry = new THREE.RingGeometry(innerRadius, outerRadius, 32);
		const ringMaterial = new THREE.MeshBasicMaterial({
			color: ringColor,
			side: THREE.DoubleSide,
			transparent: true,
			opacity: 0.8,
		});
		const ring = new THREE.Mesh(ringGeometry, ringMaterial);
		// rotate the ring to be perpendicular to the planet's axis
		ring.rotation.x = axisTilt + Math.PI / 2;
		planetGroup.add(ring);
	}

	planetGroup.name = name;
	for (const child of planetGroup.children) {
		child.name = name; // give all child objects the same name as the group
	}

	// set initial position to be random position in the planet's orbit path
	const randomAngle = Math.random() * 2 * Math.PI;
	planetGroup.position.x = orbitRadius * Math.cos(randomAngle);
	planetGroup.position.z = -orbitRadius * Math.sin(randomAngle);

	const animatePlanet = () => {
		// rotate planet about its axis (only Y-axis like real planets)
		planet.rotation.y += rotationSpeed * (rotatesClockwise ? 1 : -1);

		// calculate current angle from current position
		const currentAngle = Math.atan2(-planetGroup.position.z, planetGroup.position.x);

		// move the planet in a circular orbit
		const newAngle = currentAngle + angularVelocity;
		const newX = Math.cos(newAngle) * orbitRadius;
		const newZ = -Math.sin(newAngle) * orbitRadius; // negative to match stars' clockwise rotation
		planetGroup.position.x = newX;
		planetGroup.position.z = newZ;
	};
	return { planetGroup, animatePlanet };
}

export { initSunCore, initCorona, initSunGroup, initStars, initPlanet };
