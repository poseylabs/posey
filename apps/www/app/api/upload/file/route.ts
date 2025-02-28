import { NextResponse } from 'next/server';
import { uploadFile } from '@/utils/file-service';
import { v4 as uuidv4 } from 'uuid';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    const userId = formData.get('user_id') as string;

    if (!file) {
      return NextResponse.json({ error: 'File is required' }, { status: 400 });
    }

    const uniqueId = uuidv4().slice(0, 8); // Using first 8 characters of UUID
    const fileExtension = file.name.split('.').pop();
    const originalName = file.name.split('.').slice(0, -1).join('.');
    const uniqueFileName = `${originalName}__${uniqueId}.${fileExtension}`;

    const fileName = `user-media/${userId}/${uniqueFileName}`;
    const { url } = await uploadFile({ file, fileName });

    return NextResponse.json({ url }, { status: 200 });
  } catch (error) {
    console.error('Error uploading file:', error);
    return NextResponse.json({ error: 'Failed to upload file' }, { status: 500 });
  }
} 
