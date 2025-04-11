import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db/prisma'; // Keep prisma import for ensureUser

// Central Auth Service Endpoint - Updated Path
const AUTH_SERVICE_SESSION_URL = `${process.env.NEXT_PUBLIC_AUTH_API_ENDPOINT || 'http://localhost:9999'}/auth/session`;

// Get user info by verifying session with the central Auth service
async function verifySessionWithAuthService(req: NextRequest): Promise<{ id: string; email?: string; name?: string } | null> {
  console.log(`Verifying session with auth service: GET ${AUTH_SERVICE_SESSION_URL}`);

  // Extract cookies from the incoming request
  const cookieHeader = req.headers.get('cookie');

  if (!cookieHeader) {
    console.log('No cookies found in request to forward to auth service.');
    return null;
  }

  try {
    const response = await fetch(AUTH_SERVICE_SESSION_URL, {
      method: 'GET', // Changed to GET
      headers: {
        // Forward cookies to the auth service
        'Cookie': cookieHeader,
        // Forward the rid header for anti-csrf protection - check if needed for GET
        'rid': 'session', // SuperTokens usually checks this based on tokenTransferMethod
      },
      // No body for GET request
    });

    // Read response body regardless of status for logging
    const responseBodyText = await response.text(); 

    if (!response.ok) {
      console.error(`Auth service verify failed with status: ${response.status}`);
      console.error('Auth service response body:', responseBodyText);
      // Specific handling for 401
      if (response.status === 401) {
        console.log('Auth service returned 401 Unauthorized. Session likely invalid or expired.');
      }
      return null;
    }

    // Try to parse the successful response body as JSON
    try {
      const sessionInfo = JSON.parse(responseBodyText);
      console.log('Auth service verification successful response body:', sessionInfo);

      // Check if the response contains the expected user object and ID within it
      if (sessionInfo && sessionInfo.user && sessionInfo.user.id) {
        // Extract user details from the nested user object
        const userId = sessionInfo.user.id;
        const userEmail = sessionInfo.user.email;
        // Use username as name, or fallback if needed
        const userName = sessionInfo.user.username || sessionInfo.user.name || 'User'; 
        
        console.log(`Extracted user details: id=${userId}, email=${userEmail}, name=${userName}`);
        
        return {
          id: userId,
          email: userEmail || `${userId}@example.com`, // Use extracted email or fallback
          name: userName, // Use extracted name/username
        };
      } else {
        console.error('Auth service success response missing user object or user.id field.', sessionInfo);
        return null;
      }
    } catch (parseError) {
        console.error('Failed to parse successful auth service response as JSON:', parseError);
        console.error('Auth service raw success response body:', responseBodyText);
        return null;
    }

  } catch (error) {
    console.error('Error calling auth service for session verification:', error);
    return null;
  }
}

// Get current user by calling the central Auth Service
export async function getCurrentUser(req: NextRequest) {
  // Call the central auth service to verify the session
  const userSession = await verifySessionWithAuthService(req);

  if (!userSession) {
    console.log('getCurrentUser: No valid session found by auth service.');
    return null;
  }

  console.log('getCurrentUser: Valid session found:', userSession.id);
  return userSession; // Return the user info obtained from the auth service
}

// Middleware wrapper to protect API routes
export async function withAuth(
  request: NextRequest,
  // The handler now receives the user object returned by getCurrentUser
  handler: (req: NextRequest, user: { id: string; email?: string; name?: string }) => Promise<NextResponse>
) {
  const user = await getCurrentUser(request);

  if (!user) {
    return NextResponse.json(
      { success: false, error: 'Unauthorized' },
      { status: 401 }
    );
  }

  // Pass the validated user object to the handler
  return handler(request, user);
}

// Ensure user exists in the *inventory* database
// Note: This assumes the user ID from the auth service should match the user ID in this app's DB.
export async function ensureUser(prisma: any, user: { id: string; email?: string; name?: string }) {
  if (!user || !user.id) {
    console.error('ensureUser called with invalid user:', user);
    return null;
  }

  try {
    console.log('Ensuring user exists in Inventory DB with ID:', user.id);

    const existingUser = await prisma.user.findUnique({
      where: { id: user.id },
    });

    if (existingUser) {
      console.log('Found existing user in Inventory DB');
      return existingUser;
    }

    console.log('User not found in Inventory DB, creating new user record:', user.id);
    // Use details from the validated session
    return await prisma.user.create({
      data: {
        id: user.id,
        email: user.email || `${user.id}@example.com`, // Use provided email or fallback
        name: user.name || 'User', // Use provided name or fallback
      },
    });
  } catch (error) {
    console.error('Error ensuring user exists in Inventory DB:', error);
    return null;
  }
} 