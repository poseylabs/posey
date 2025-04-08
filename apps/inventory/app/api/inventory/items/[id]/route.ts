import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { successResponse, errorResponse } from '@/lib/utils';

// GET /api/inventory/items/[id] - Get a single item
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const item = await prisma.item.findUnique({
      where: { id },
      include: {
        pod: true,
      },
    });

    if (!item) {
      return errorResponse('Item not found', 404);
    }

    return successResponse(item);
  } catch (error) {
    console.error('Error fetching item:', error);
    return errorResponse('Failed to fetch item');
  }
}

// PUT /api/inventory/items/[id] - Update an item
export async function PUT(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await req.json();
    const item = await prisma.item.update({
      where: { id },
      data: body,
      include: {
        pod: true,
      },
    });

    return successResponse(item);
  } catch (error) {
    console.error('Error updating item:', error);
    return errorResponse('Failed to update item');
  }
}

// DELETE /api/inventory/items/[id] - Delete an item
export async function DELETE(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    await prisma.item.delete({
      where: { id },
    });

    return successResponse({ message: 'Item deleted successfully' });
  } catch (error) {
    console.error('Error deleting item:', error);
    return errorResponse('Failed to delete item');
  }
}
