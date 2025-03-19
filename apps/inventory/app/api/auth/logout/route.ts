import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { successResponse } from '@/lib/utils';

// Logout route handler
export async function POST(_req: NextRequest) {
  // Create response with success message
  const response = NextResponse.json({
    success: true,
    data: { message: 'Logged out successfully' }
  });

  // Clear the authentication cookie
  response.cookies.delete('sAccessToken');

  return response;
} 