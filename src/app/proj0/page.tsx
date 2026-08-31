import Image from "next/image";
import { getAssetPath } from "@/shared"

export default function Page() {
	return (
        <main className="mx-4 my-2 sm:mx-8 space-y-4">
            <p>Project 0: Becoming Friends with Your Camera</p>
            <p>Part 1: pictures of myself from up close and from further away</p>
            <div className="flex flex-row justify-center space-x-20">
            <Image
                key={"face1"}
                src={getAssetPath("/proj0/face1.jpeg")}
                alt={"Me! up close"}
                height={200}
                width={200}
                style={{ width: "200px", height: 'auto' }} 
                className="rounded-md"
                />
            <Image
                key={"face2"}
                src={getAssetPath("/proj0/face2.jpeg")}
                alt={"My face from a little further away..."}
                height={200}
                width={200}
                style={{ width: "200px", height: 'auto' }} 
                className="rounded-md"
                />
            <Image
                key={"face3"}
                src={getAssetPath("/proj0/face3.jpeg")}
                alt={"My face from even further away..."}
                height={200}
                width={200}
                style={{ width: "200px", height: 'auto' }} 
                className="rounded-md"
                />
            <Image
                key={"face4"}
                src={getAssetPath("/proj0/face4.jpeg")}
                alt={"My face from EVEN further away..."}
                height={200}
                width={200}
                style={{ width: "200px", height: 'auto' }} 
                className="rounded-md"
                />
            <Image
                key={"face5"}
                src={getAssetPath("/proj0/face5.jpeg")}
                alt={"My face from far away, zoomed in!"}
                height={200}
                width={200}
                style={{ width: "200px", height: 'auto' }} 
                className="rounded-md"
                />
            </div>

            <p>Part 2: two pictures of Wheeler Hall. I took the first picture from afar, zooming into Wheeler Hall's facade. Then, I walked closer and took a second picture without any zoom.</p>
            <div className="flex flex-row justify-center space-x-20">
            <Image
                key={"face1"}
                src={getAssetPath("/proj0/architecture1.jpeg")}
                alt={"Wheeler Hall from afar, zoomed in"}
                height={300}
                width={300}
                style={{ width: "45vh", height: 'auto' }} 
                className="rounded-md"
                />
            <Image
                key={"face2"}
                src={getAssetPath("/proj0/architecture2.jpeg")}
                alt={"Wheeler Hall from up close, without zoom"}
                height={300}
                width={300}
                style={{ width: "45vh", height: 'auto' }} 
                className="rounded-md"
                />

            </div>
        </main>
	);
}