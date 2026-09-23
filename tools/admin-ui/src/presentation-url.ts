/** A shared Admin mount stays on its current origin, including Quick Tunnels. */
export function presentationUrl(page: URL, configured?: string): string | undefined {
  if (!configured) return undefined;
  return page.pathname === "/admin" || page.pathname.startsWith("/admin/")
    ? new URL("/", page).href
    : configured;
}
