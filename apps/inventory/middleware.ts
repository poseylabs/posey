import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Basic middleware for forwarding necessary headers (like cookies)
// No session verification here; that happens in the API route via withAuth.
export async function middleware(request: NextRequest) {
  // Optionally log path or headers for debugging
  // console.log('Middleware Path:', request.nextUrl.pathname);
  
  // Just pass the request through. The main purpose is to ensure
  // the matcher runs and potentially modify headers if needed in the future.
  // For now, we let API routes handle their own auth checks.
  return NextResponse.next({
    request: {
      // Pass original headers (including cookies needed for auth service)
      headers: new Headers(request.headers),
    },
  });
}

// Configure which paths this middleware runs on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - Static assets
     * This ensures API routes and pages are processed.
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}; 