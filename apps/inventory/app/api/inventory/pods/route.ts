import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { successResponse, errorResponse } from '@/lib/utils';
import { withAuth, ensureUser } from '@/lib/auth';

// GET /api/inventory/pods - Get all pods
export async function GET(req: NextRequest) {
  return withAuth(req, async (request, user) => {
    try {
      // Ensure user exists in our database
      const dbUser = await ensureUser(prisma, user);
      if (!dbUser) {
        return errorResponse('User not found', 404);
      }

      const url = new URL(request.url);
      const parentId = url.searchParams.get('parentId');

      const pods = await prisma.storagePod.findMany({
        where: {
          userId: dbUser.id,
          parentId: parentId || null,
        },
        include: {
          childPods: true,
          items: true,
        },
      });

      return successResponse(pods);
    } catch (error) {
      console.error('Error fetching pods:', error);
      return errorResponse('Failed to fetch storage pods');
    }
  });
}

// POST /api/inventory/pods - Create a new pod
export async function POST(req: NextRequest) {
  return withAuth(req, async (request, user) => {
    try {
      // Ensure user exists in our database
      const dbUser = await ensureUser(prisma, user);
      if (!dbUser) {
        return errorResponse('User not found', 404);
      }

      const body = await request.json();

      const pod = await prisma.storagePod.create({
        data: {
          ...body,
          userId: dbUser.id,
        },
      });

      return successResponse(pod, 201);
    } catch (error) {
      console.error('Error creating pod:', error);
      return errorResponse(`Failed to create storage pod: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  });
} 