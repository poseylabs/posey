import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { successResponse, errorResponse, generateQRCode } from '@/lib/utils';

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const podId = url.searchParams.get('podId');

    if (!podId) {
      return errorResponse('Pod ID is required', 400);
    }

    const pod = await prisma.storagePod.findUnique({
      where: { id: podId },
    });

    if (!pod) {
      return errorResponse('Pod not found', 404);
    }

    // Generate QR code URL - this would be replaced with actual QR code generation in production
    const qrCodeUrl = generateQRCode(pod.id);

    const labelData = {
      id: pod.id,
      title: pod.title,
      description: pod.description,
      qrCodeUrl,
      color: pod.color,
      size: pod.size,
      location: pod.location,
    };

    return successResponse(labelData);
  } catch (error) {
    console.error('Error generating label:', error);
    return errorResponse('Failed to generate label');
  }
} 