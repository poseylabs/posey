import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { successResponse, errorResponse } from '@/lib/utils';

// GET /api/inventory/pods/[id] - Get a single pod
export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const pod = await prisma.storagePod.findUnique({
      where: {
        id: params.id,
      },
      include: {
        childPods: true,
        items: true,
      },
    });

    if (!pod) {
      return errorResponse('Storage pod not found', 404);
    }

    return successResponse(pod);
  } catch (error) {
    console.error('Error fetching pod:', error);
    return errorResponse('Failed to fetch storage pod');
  }
}

// PUT /api/inventory/pods/[id] - Update a pod
export async function PUT(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await req.json();
    const pod = await prisma.storagePod.update({
      where: {
        id: params.id,
      },
      data: body,
    });

    return successResponse(pod);
  } catch (error) {
    console.error('Error updating pod:', error);
    return errorResponse('Failed to update storage pod');
  }
}

// DELETE /api/inventory/pods/[id] - Delete a pod
export async function DELETE(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Check if pod has items or child pods
    const pod = await prisma.storagePod.findUnique({
      where: { id: params.id },
      include: { items: true, childPods: true },
    });

    if (!pod) {
      return errorResponse('Storage pod not found', 404);
    }

    if (pod.items.length > 0 || pod.childPods.length > 0) {
      return errorResponse('Cannot delete pod with items or child pods', 400);
    }

    await prisma.storagePod.delete({
      where: { id: params.id },
    });

    return successResponse({ message: 'Pod deleted successfully' });
  } catch (error) {
    console.error('Error deleting pod:', error);
    return errorResponse('Failed to delete storage pod');
  }
} 