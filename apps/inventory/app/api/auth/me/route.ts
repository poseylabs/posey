import { NextRequest } from 'next/server';
import { successResponse, errorResponse } from '@/lib/utils';
import { prisma } from '@/lib/db/prisma';
import { withAuth, ensureUser } from '@/lib/auth';

// Get current user route handler
export async function GET(req: NextRequest) {
  return withAuth(req, async (_, user) => {
    try {
      // Ensure user exists in the database
      const dbUser = await ensureUser(prisma, user);
      if (!dbUser) {
        return errorResponse('User not found', 404);
      }

      return successResponse({
        user: {
          id: dbUser.id,
          email: dbUser.email,
          name: dbUser.name,
        }
      });
    } catch (error) {
      console.error('Error fetching current user:', error);
      return errorResponse('Failed to fetch user information');
    }
  });
} 