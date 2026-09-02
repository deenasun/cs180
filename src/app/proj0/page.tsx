import Image from "next/image";
import { getAssetPath } from "@/shared"
import Gif from "@/components/Gif"

const dollyZoomImages = [
    "/proj0/dolly_zoom/dolly_zoom1.jpeg",
    "/proj0/dolly_zoom/dolly_zoom2.jpeg",
    "/proj0/dolly_zoom/dolly_zoom3.jpeg",
    "/proj0/dolly_zoom/dolly_zoom4.jpeg",
    "/proj0/dolly_zoom/dolly_zoom5.jpeg",
    "/proj0/dolly_zoom/dolly_zoom6.jpeg",
    "/proj0/dolly_zoom/dolly_zoom7.jpeg",
    "/proj0/dolly_zoom/dolly_zoom8.jpeg",
    "/proj0/dolly_zoom/dolly_zoom9.jpeg",
    "/proj0/dolly_zoom/dolly_zoom10.jpeg",
    "/proj0/dolly_zoom/dolly_zoom11.jpeg",
    "/proj0/dolly_zoom/dolly_zoom12.jpeg",
    "/proj0/dolly_zoom/dolly_zoom13.jpeg",
    "/proj0/dolly_zoom/dolly_zoom14.jpeg",
    "/proj0/dolly_zoom/dolly_zoom15.jpeg",
    "/proj0/dolly_zoom/dolly_zoom16.jpeg",
]

export default function Page() {
    return (
        <main className="mx-4 my-2 sm:mx-8 space-y-4 justify-center">
            <p>Project 0: Becoming Friends with Your Camera</p>
            <p>Part 1: pictures of myself from up close and from further away</p>
            <div className="flex flex-row justify-center space-x-20">
                <Image
                    key={"face1"}
                    src={getAssetPath("/proj0/face1.jpeg")}
                    alt={"Me! up close"}
                    height={1440}
                    width={1080}
                    style={{ width: "10vw", height: 'auto' }}
                    className="rounded-md"
                />
                <Image
                    key={"face2"}
                    src={getAssetPath("/proj0/face2.jpeg")}
                    alt={"My face from a little further away..."}
                    height={1440}
                    width={1080}
                    style={{ width: "10vw", height: 'auto' }}
                    className="rounded-md"
                />
                <Image
                    key={"face3"}
                    src={getAssetPath("/proj0/face3.jpeg")}
                    alt={"My face from even further away..."}
                    height={1440}
                    width={1080}
                    style={{ width: "10vw", height: 'auto' }}
                    className="rounded-md"
                />
                <Image
                    key={"face4"}
                    src={getAssetPath("/proj0/face4.jpeg")}
                    alt={"My face from EVEN further away..."}
                    height={1440}
                    width={1080}
                    style={{ width: "10vw", height: 'auto' }}
                    className="rounded-md"
                />
                <Image
                    key={"face5"}
                    src={getAssetPath("/proj0/face5.jpeg")}
                    alt={"My face from far away, zoomed in!"}
                    height={1440}
                    width={1080}
                    style={{ width: "10vw", height: 'auto' }}
                    className="rounded-md"
                />
            </div>

            <p>Part 2: two pictures of Wheeler Hall. I took the first picture from afar, zooming into Wheeler Hall's facade. Then, I walked closer and took a second picture without any zoom.</p>
            <div className="flex flex-row justify-center space-x-20">
                <Image
                    key={"face1"}
                    src={getAssetPath("/proj0/architecture1.jpeg")}
                    alt={"Wheeler Hall from afar, zoomed in"}
                    height={1080}
                    width={1440}
                    style={{ width: "25vw", height: 'auto' }}
                    className="rounded-md"
                />
                <Image
                    key={"face2"}
                    src={getAssetPath("/proj0/architecture2.jpeg")}
                    alt={"Wheeler Hall from up close, without zoom"}
                    height={1080}
                    width={1440}
                    style={{ width: "25vw", height: 'auto' }}
                    className="rounded-md"
                />
            </div>

            <p>Part 3: A dolly zoom of Sather Gate!</p>
            <div className="flex flex-row justify-center space-x-20">
            <Gif imagePaths={dollyZoomImages} />
            </div>
        </main>
    );
}
