export const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? ""

export function getAssetPath(path: string) {
  return `${basePath}${path}`;
}