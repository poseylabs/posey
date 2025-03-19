import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { successResponse, errorResponse } from '@/lib/utils';

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const query = url.searchParams.get('q') || '';
    const type = url.searchParams.get('type'); // 'pods', 'items', or null for both
    const color = url.searchParams.get('color');
    const size = url.searchParams.get('size');
    const location = url.searchParams.get('location');
    const userId = url.searchParams.get('userId') || 'demo-user'; // In production, you'd get this from auth

    if (!query && !color && !size && !location) {
      return errorResponse('At least one search parameter is required', 400);
    }

    // Define common filter conditions
    const titleFilter = query ? { title: { contains: query, mode: 'insensitive' } } : {};
    const descriptionFilter = query ? { description: { contains: query, mode: 'insensitive' } } : {};
    const colorFilter = color ? { color: { contains: color, mode: 'insensitive' } } : {};
    const sizeFilter = size ? { size: { contains: size, mode: 'insensitive' } } : {};
    const locationFilter = location ? { location: { contains: location, mode: 'insensitive' } } : {};
    const userFilter = { userId };

    let results: { pods?: any[]; items?: any[] } = {};

    // Search in pods if type is 'pods' or not specified
    if (!type || type === 'pods') {
      const pods = await prisma.storagePod.findMany({
        where: {
          AND: [
            userFilter,
            {
              OR: [
                titleFilter,
                descriptionFilter,
              ],
            },
            colorFilter,
            sizeFilter,
            locationFilter,
          ],
        },
        include: {
          _count: {
            select: {
              items: true,
              childPods: true,
            },
          },
        },
      });
      results.pods = pods;
    }

    // Search in items if type is 'items' or not specified
    if (!type || type === 'items') {
      const items = await prisma.item.findMany({
        where: {
          AND: [
            userFilter,
            {
              OR: [
                titleFilter,
                descriptionFilter,
              ],
            },
            colorFilter,
            sizeFilter,
            locationFilter,
          ],
        },
        include: {
          pod: {
            select: {
              id: true,
              title: true,
            },
          },
        },
      });
      results.items = items;
    }

    return successResponse(results);
  } catch (error) {
    console.error('Error searching inventory:', error);
    return errorResponse('Failed to search inventory');
  }
} 