import { NextRequest, NextResponse } from 'next/server';
import * as jose from 'jose'; // Added import for JWT verification

// Function to verify JWT token
export async function verifyToken(token: string) {
  try {
    // Assume the token is a JWT and needs verification
    // You MUST set a secret key in your environment variables (e.g., JWT_SECRET)
    const secret = new TextEncoder().encode(process.env.JWT_SECRET || 'your-fallback-secret-key-here'); // Replace with your actual secret key mechanism

    // Verify the token and decode the payload
    const { payload } = await jose.jwtVerify(token, secret);

    console.log('Verified token payload:', payload);
    // Return the payload which should contain user info (e.g., sub for user ID)
    return payload;

  } catch (error) {
    console.error('Error verifying token:', error);
    // Distinguish between verification errors and other errors
    if (error instanceof jose.errors.JWTExpired || error instanceof jose.errors.JWTClaimValidationFailed || error instanceof jose.errors.JWSSignatureVerificationFailed) {
        console.warn('Token validation failed:', error.message);
    } else {
        console.error('An unexpected error occurred during token verification:', error);
    }
    return null; // Return null if verification fails
  }
}

// Get the session token from cookies or headers
export function getAccessToken(req?: NextRequest) {
  try {
    // If request object is provided, check for x-auth-token header first
    if (req) {
      const headerToken = req.headers.get('x-auth-token');
      if (headerToken) {
        return headerToken;
      }

      // Also check Authorization header
      const authHeader = req.headers.get('Authorization');
      if (authHeader?.startsWith('Bearer ')) {
        return authHeader.substring(7);
      }

      // Check request cookies directly
      const authToken = req.cookies.get('authToken')?.value;
      const stAccessToken = req.cookies.get('sAccessToken')?.value;

      if (authToken || stAccessToken) {
        return authToken || stAccessToken;
      }
    }

    // Don't attempt to use cookies() from next/headers in server components
    // since it can behave differently in different contexts
    return null;
  } catch (error) {
    console.error('Error accessing token:', error);
    return null;
  }
}

// Get user ID from request headers (added by middleware)
export function getUserId(req?: NextRequest) {
  if (!req) return null;
  return req.headers.get('x-user-id') || null;
}

// Get current user from session
export async function getCurrentUser(req?: NextRequest) {
  // First, try to get the user ID from request headers (this is most reliable)
  const userId = getUserId(req);
  console.log('x-user-id from headers:', userId);

  if (userId) {
    // If we have a user ID in the headers, create a minimal user object
    console.log('Using user ID from headers:', userId);
    return {
      id: userId,
      email: `${userId}@example.com`, // We don't have the actual email, but we need something
      name: 'User',
    };
  }

  // If no user ID header, check for SuperTokens session tokens in cookies
  if (req) {
    const stAccessToken = req.cookies.get('sAccessToken')?.value;
    const frontToken = req.cookies.get('sFrontToken')?.value;

    if (stAccessToken && frontToken) {
      try {
        // Try to extract user ID from the front token which is less secure but simpler
        // In a production app, you'd want to properly decode and verify these tokens
        if (frontToken.includes('uid')) {
          const frontTokenData = JSON.parse(Buffer.from(frontToken, 'base64').toString());
          if (frontTokenData && frontTokenData.uid) {
            console.log('Extracted user ID from SuperTokens front token:', frontTokenData.uid);
            return {
              id: frontTokenData.uid,
              email: `${frontTokenData.uid}@example.com`,
              name: 'User',
            };
          }
        }
      } catch (err) {
        console.error('Error parsing SuperTokens front token:', err);
      }
    }
  }

  // If no user ID header or valid SuperTokens session, try token-based auth as fallback
  const token = getAccessToken(req);
  console.log('Auth token present:', !!token);
  if (!token) {
    return null;
  }

  try {
    // Verify the token and get the payload
    const payload = await verifyToken(token);

    if (!payload || !payload.sub) {
      console.error('Token verification failed or missing sub claim');
      return null;
    }

    // Use the 'sub' claim (subject) as the user ID, which is standard for JWTs
    const userIdFromToken = payload.sub;
    console.log('Using user ID from verified token:', userIdFromToken);

    return {
      id: userIdFromToken,
      // You might get email/name from the token payload as well, if available
      email: (payload.email as string) || `${userIdFromToken}@example.com`,
      name: (payload.name as string) || 'User',
    };

  } catch (error) {
    console.error('Error getting current user from token:', error);
    return null;
  }
}

// Middleware to protect API routes
export async function withAuth(
  request: NextRequest,
  handler: (req: NextRequest, user: any) => Promise<NextResponse>
) {
  const user = await getCurrentUser(request);

  if (!user) {
    return NextResponse.json(
      { success: false, error: 'Unauthorized' },
      { status: 401 }
    );
  }

  return handler(request, user);
}

// Ensure user exists in the database
export async function ensureUser(prisma: any, user: any) {
  if (!user || !user.id) {
    console.error('ensureUser called with invalid user:', user);
    return null;
  }

  try {
    console.log('Looking for user with ID:', user.id);

    // First, try to find the user by ID
    const existingUser = await prisma.user.findUnique({
      where: { id: user.id },
    });

    if (existingUser) {
      console.log('Found existing user by ID');
      return existingUser;
    }

    // If not found by ID, the user might exist with a different ID but same email
    // We don't have email in this context though, so we need to create the user
    console.log('User not found by ID, creating new user with ID:', user.id);
    return await prisma.user.create({
      data: {
        id: user.id,
        email: user.email || `${user.id}@example.com`, // Fallback email if not provided
        name: user.name || 'User',
      },
    });
  } catch (error) {
    console.error('Error ensuring user exists:', error);
    console.error('Error details:', error instanceof Error ? error.message : String(error));
    return null;
  }
} 