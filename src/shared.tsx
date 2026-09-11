// GitHub Pages serves the static export from /cs180 instead of the domain root,
// so local asset URLs need this prefix in production.
export const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? ""

export function getAssetPath(path: string) {
  // Return external links as-is
  if (path.startsWith("http:") || path.startsWith("https:")) {
    return path;
  }
  // Prefix file paths of local assets (e.g. in public/) with the
  // right base path based on whether the app is being served locally or from /cs180
  return `${basePath}${path}`;
}
