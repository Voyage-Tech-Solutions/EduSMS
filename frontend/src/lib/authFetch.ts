/**
 * Authenticated fetch wrapper.
 * Drop-in replacement for fetch() that automatically injects
 * the Supabase JWT as an Authorization: Bearer header.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function authFetch(
  input: string,
  init?: RequestInit
): Promise<Response> {
  // Rewrite relative /api/v1/ paths to the backend base URL
  let url = input;
  if (url.startsWith('/api/v1/')) {
    url = `${API_BASE_URL}${url.slice(7)}`;
  } else if (url.startsWith('/api/v1')) {
    url = API_BASE_URL;
  }

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

  return fetch(url, {
    ...init,
    headers: {
      ...authHeader,
      ...existingHeaders,
    },
  });
}
