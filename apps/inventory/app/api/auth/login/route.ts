import { NextRequest, NextResponse } from 'next/server';
import { SignJWT } from 'jose';
import { prisma } from '@/lib/db/prisma';
import { errorResponse } from '@/lib/utils';
import bcrypt from 'bcrypt';

// Function to get JWT secret
const getJWTSecret = () => {
  const secret = process.env.JWT_SECRET || 'posey-inventory-secret-key-for-development-only';
  return new TextEncoder().encode(secret);
};

// Login route handler
export async function POST(req: NextRequest) {
  try {
    const { email, password } = await req.json();

    if (!email || !password) {
      return errorResponse('Email and password are required', 400);
    }

    // Find user by email
    const user = await prisma.user.findUnique({
      where: { email },
    });

    if (!user || !user.passwordHash) {
      return errorResponse('Invalid email or password', 401);
    }

    // Verify password
    const passwordMatch = await bcrypt.compare(password, user.passwordHash);

    if (!passwordMatch) {
      return errorResponse('Invalid email or password', 401);
    }

    // Create JWT token
    const token = await new SignJWT({
      sub: user.id,
      email: user.email,
      name: user.name || '',
    })
      .setProtectedHeader({ alg: 'HS256' })
      .setIssuedAt()
      .setExpirationTime('24h')
      .sign(getJWTSecret());

    // Create response with user data
    const response = NextResponse.json({
      success: true,
      data: {
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
        },
      }
    });

    // Set the cookie in the response
    response.cookies.set({
      name: 'sAccessToken',
      value: token,
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 60 * 60 * 24, // 24 hours
    });

    return response;
  } catch (error) {
    console.error('Login error:', error);
    return errorResponse('Authentication failed');
  }
} 