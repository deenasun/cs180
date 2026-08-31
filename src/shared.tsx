export const basePath =
  process.env.GITHUB_ACTIONS === "true" ? "/cs180" : "";

export function getAssetPath(path: string) {
  return `${basePath}${path}`;
}