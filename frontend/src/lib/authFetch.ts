/**
 * Authenticated fetch wrapper.
 * Drop-in replacement for fetch() that automatically injects
 * the Supabase JWT as an Authorization: Bearer header.
 *
 * URLs are kept as-is (relative paths like /api/v1/... go through
 * the Next.js rewrite proxy, avoiding CORS entirely).
 */

export async function authFetch(
  input: string,
  init?: RequestInit
): Promise<Response> {
  // Get auth token from Supabase session
  let authHeader: Record<string, string> = {};
  try {
    const { getSession } = await import('./supabase');
    const session = await getSession();
    if (session?.access_token) {
      authHeader = { Authorization: `Bearer ${session.access_token}` };
    }
  } catch {
    // No session available — request will proceed without auth
  }

  // Merge auth header with any caller-provided headers
  const existingHeaders: Record<string, string> = init?.headers
    ? init.headers instanceof Headers
      ? Object.fromEntries(init.headers.entries())
      : Array.isArray(init.headers)
        ? Object.fromEntries(init.headers)
        : (init.headers as Record<string, string>)
    : {};

  return fetch(input, {
    ...init,
    headers: {
      ...authHeader,
      ...existingHeaders,
    },
  });
}
