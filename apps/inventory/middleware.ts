import { NextRequest, NextResponse } from 'next/server';

// Paths that don't require authentication
const PUBLIC_PATHS = [
  '/auth/login',
  '/auth/register',
  '/api/auth/login',
  '/api/auth/register',
  '/api/auth/logout',
  '/api/health',
];

// Check if a path is public (doesn't require authentication)
const isPublicPath = (path: string) => {
  return PUBLIC_PATHS.some(publicPath =>
    path === publicPath ||
    path.startsWith('/auth/') ||
    path.startsWith('/api/auth/') ||
    path.startsWith('/_next/') ||
    path.includes('/favicon') ||
    path.includes('.svg') ||
    path.includes('.png') ||
    path.includes('.jpg') ||
    path.includes('.css') ||
    path.includes('.js')
  );
};

export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;

  // Allow public paths without authentication
  if (isPublicPath(path)) {
    return NextResponse.next();
  }

  // Only protect API routes - let AuthProvider handle page routes
  if (path.startsWith('/api/')) {
    // Check for token in cookies
    const cookieToken = request.cookies.get('authToken')?.value;

    // Check for token in Authorization header
    const authHeader = request.headers.get('Authorization');
    const headerToken = authHeader?.startsWith('Bearer ')
      ? authHeader.substring(7)
      : null;

    // Check for user ID header as additional auth method
    const userIdHeader = request.headers.get('X-User-Id');

    // Check SuperTokens cookies
    const stAccessToken = request.cookies.get('sAccessToken')?.value;
    const stRefreshToken = request.cookies.get('sRefreshToken')?.value;
    const frontToken = request.cookies.get('sFrontToken')?.value;

    // Try to extract user ID from SuperTokens cookies if not in header
    let userId = userIdHeader;
    if (!userId && frontToken && frontToken.includes('uid')) {
      try {
        const frontTokenData = JSON.parse(Buffer.from(frontToken, 'base64').toString());
        if (frontTokenData && frontTokenData.uid) {
          userId = frontTokenData.uid;
          console.log('Extracted user ID from SuperTokens front token:', userId);
        }
      } catch (err) {
        console.error('Error parsing SuperTokens front token:', err);
      }
    }

    // Use any available auth method
    const hasToken = headerToken || cookieToken || stAccessToken;
    const hasUserId = !!userId;

    // Allow the request if we have either a token or a user ID (or both)
    if (!hasToken && !hasUserId) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Continue with the valid auth info
    const requestHeaders = new Headers(request.headers);
    if (hasToken) {
      requestHeaders.set('x-auth-token', headerToken || cookieToken || stAccessToken || '');
    }
    if (hasUserId) {
      requestHeaders.set('x-user-id', userId || '');
    }

    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    });
  }

  // For all other routes, let the AuthProvider handle authentication
  return NextResponse.next();
}

// Configure which paths this middleware runs on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image).*)',
  ],
}; 