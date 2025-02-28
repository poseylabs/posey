import { v4, v5 } from 'uuid';
import { NextRequest, NextResponse } from 'next/server';

const AGENT_NAMESPACE = process.env.NEXT_PUBLIC_AGENT_NAMESPACE || process.env.AGENT_NAMESPACE || '1b671a64-40d5-491e-99b0-da01ff1f3341';

// Generate deterministic UUID based on agent type
const generateV5 = (name: string, namespace: string = AGENT_NAMESPACE): string => {
  if (!name || typeof name !== 'string') {
    throw new Error('Invalid uuid name provided');
  }
  return v5(name, namespace);
};

const generateUUID = () => {
  return v4();
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ version: string }> }
) {
  const { version } = await params;

  const searchParams = request.nextUrl.searchParams;
  const name = searchParams.get('name');
  const namespace = searchParams.get('namespace') || AGENT_NAMESPACE;
  const _version = version?.toLowerCase();

  let _id = generateUUID();

  if (_version === 'v5' && typeof name === 'string') {
    _id = generateV5(name, namespace);
  }

  return NextResponse.json({
    uuid: _id,
    success: true
  }, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET'
    },
  });
}

// Optional: Add OPTIONS handler if needed for CORS
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET'
    },
  });
}
