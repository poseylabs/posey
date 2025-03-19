import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { successResponse, errorResponse } from '@/lib/utils';
import { withAuth, ensureUser } from '@/lib/auth';

// GET /api/inventory/locations - Get all locations
export async function GET(req: NextRequest) {
  console.log('GET /api/inventory/locations request received');
  return withAuth(req, async (request, user) => {
    try {
      console.log('User from withAuth:', user);
      // Ensure user exists in our database
      const dbUser = await ensureUser(prisma, user);
      console.log('DB User result:', dbUser ? 'found' : 'not found');
      if (!dbUser) {
        return errorResponse('User not found', 404);
      }

      const locations = await prisma.location.findMany({
        where: {
          userId: dbUser.id,
        },
        orderBy: {
          name: 'asc',
        },
      });
      console.log(`Found ${locations.length} locations for user ${dbUser.id}`);

      return successResponse(locations);
    } catch (error) {
      console.error('Error fetching locations:', error);
      return errorResponse('Failed to fetch locations');
    }
  });
}

// POST /api/inventory/locations - Create a new location
export async function POST(req: NextRequest) {
  console.log('POST /api/inventory/locations request received');
  return withAuth(req, async (request, user) => {
    try {
      console.log('User from withAuth:', user);
      // Ensure user exists in our database
      const dbUser = await ensureUser(prisma, user);
      console.log('DB User result:', dbUser ? 'found' : 'not found');
      if (!dbUser) {
        return errorResponse('User not found', 404);
      }

      const body = await request.json();
      console.log('Received location data:', body);

      const location = await prisma.location.create({
        data: {
          ...body,
          userId: dbUser.id,
        },
      });
      console.log('Created location:', location);

      return successResponse(location, 201);
    } catch (error) {
      console.error('Error creating location:', error);
      return errorResponse(`Failed to create location: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  });
} 