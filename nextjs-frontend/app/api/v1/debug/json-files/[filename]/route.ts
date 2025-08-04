import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    const filename = decodeURIComponent(params.filename);
    const response = await fetch(`${BACKEND_URL}/api/v1/debug/json-files/${encodeURIComponent(filename)}`);

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching JSON file content:', error);
    return NextResponse.json(
      { error: 'Failed to fetch document content' },
      { status: 500 }
    );
  }
}
