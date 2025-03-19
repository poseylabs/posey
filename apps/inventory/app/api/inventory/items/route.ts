import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { successResponse, errorResponse } from '@/lib/utils';
import { withAuth, ensureUser } from '@/lib/auth';

// GET /api/inventory/items - Get all items
export async function GET(req: NextRequest) {
  return withAuth(req, async (request, user) => {
    try {
      // Ensure user exists in our database
      const dbUser = await ensureUser(prisma, user);
      if (!dbUser) {
        return errorResponse('User not found', 404);
      }

      const url = new URL(request.url);
      const podId = url.searchParams.get('podId');

      const items = await prisma.item.findMany({
        where: {
          userId: dbUser.id,
          ...(podId ? { podId } : {}),
        },
        include: {
          pod: true,
        },
      });

      return successResponse(items);
    } catch (error) {
      console.error('Error fetching items:', error);
      return errorResponse('Failed to fetch items');
    }
  });
}

// POST /api/inventory/items - Create a new item
export async function POST(req: NextRequest) {
  return withAuth(req, async (request, user) => {
    try {
      // Ensure user exists in our database
      const dbUser = await ensureUser(prisma, user);
      if (!dbUser) {
        return errorResponse('User not found', 404);
      }

      const body = await request.json();

      const item = await prisma.item.create({
        data: {
          ...body,
          userId: dbUser.id,
        },
        include: {
          pod: true,
        },
      });

      return successResponse(item, 201);
    } catch (error) {
      console.error('Error creating item:', error);
      return errorResponse(`Failed to create item: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  });
} 