import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getSession } from '@posey.ai/core/helpers';

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if the path starts with /admin
  if (pathname.startsWith('/admin')) {
    console.log(`Middleware triggered for admin path: ${pathname}`);
    try {
      // Attempt to get the session info
      // Note: We need to handle potential errors if the auth service is down
      console.log('Middleware: Calling getSession...');
      // Pass the request headers to getSession
      const sessionInfo = await getSession(request.headers);
      console.log('Middleware: getSession returned:', JSON.stringify(sessionInfo, null, 2)); // Log the full result

      // Extract role for logging
      const userRole = sessionInfo?.user?.role;
      console.log(`Middleware: Checking user role. Found role: ${userRole}`);

      // Check if session exists and user role is admin
      if (!sessionInfo?.user || userRole !== 'admin') {
        console.log(`Middleware: Admin access denied. Role was ${userRole}. Redirecting to login.`);
        // Redirect non-admins trying to access admin pages
        const loginUrl = new URL('/auth/login', request.url);
        loginUrl.searchParams.set('redirect', pathname);
        return NextResponse.redirect(loginUrl);
      }

      console.log('Admin access granted.');
      // User is admin, allow the request to proceed
      return NextResponse.next();
    } catch (error) {
      console.error('Middleware error fetching session:', error);
      // Handle errors (e.g., auth service down) - maybe redirect to an error page or login
      const loginUrl = new URL('/auth/login', request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  // For non-admin paths, allow the request to proceed
  return NextResponse.next();
}

// Configure the middleware to run only on /admin/* paths
export const config = {
  matcher: '/admin/:path*',
}; 