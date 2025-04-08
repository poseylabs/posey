import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { Prisma } from '@prisma/client';
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

    // Allow search even if only type is specified, refine check
    if (!query && !color && !size && !location && !type) {
      return errorResponse('At least one search parameter (q, color, size, location) or type is required', 400);
    }

    const userFilter = { userId };

    // --- Construct Pod Where Clause ---
    const podWhereConditions: Prisma.StoragePodWhereInput[] = [userFilter];
    if (query) {
      podWhereConditions.push({
        OR: [
          { title: { contains: query, mode: Prisma.QueryMode.insensitive } },
          { description: { contains: query, mode: Prisma.QueryMode.insensitive } },
        ],
      });
    }
    const podWhere: Prisma.StoragePodWhereInput = { AND: podWhereConditions };


    // --- Construct Item Where Clause ---
    const itemWhereConditions: Prisma.ItemWhereInput[] = [userFilter];
    if (query) {
      itemWhereConditions.push({
        OR: [
          { title: { contains: query, mode: Prisma.QueryMode.insensitive } },
          { description: { contains: query, mode: Prisma.QueryMode.insensitive } },
        ],
      });
    }
    if (color) {
      itemWhereConditions.push({ color: { contains: color, mode: Prisma.QueryMode.insensitive } });
    }
    if (size) {
      itemWhereConditions.push({ size: { contains: size, mode: Prisma.QueryMode.insensitive } });
    }
    if (location) {
      itemWhereConditions.push({ location: { contains: location, mode: Prisma.QueryMode.insensitive } });
    }
    const itemWhere: Prisma.ItemWhereInput = { AND: itemWhereConditions };


    const results: { pods?: any[]; items?: any[] } = {};

    // Search in pods
    if (!type || type === 'pods') {
      const pods = await prisma.storagePod.findMany({
        where: podWhere,
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

    // Search in items
    if (!type || type === 'items') {
      const items = await prisma.item.findMany({
        where: itemWhere,
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

    const resultsArray = [
      ...(results.items?.map((item) => ({ ...item, type: "item" })) || []),
      ...(results.pods?.map((pod) => ({ ...pod, type: "pod" })) || []),
    ];

    return successResponse(resultsArray);
  } catch (error) {
    console.error('Error searching inventory:', error);
    return errorResponse('Failed to search inventory');
  }
} 