import { S3Client, PutObjectCommand, ObjectCannedACL } from '@aws-sdk/client-s3';

const getOriginEndpoint = () => {
  if (!process.env.DO_STORAGE_ORIGIN_ENDPOINT) {
    throw new Error('DO_STORAGE_ORIGIN_ENDPOINT env variable is not set');
  }
  return process.env.DO_STORAGE_ORIGIN_ENDPOINT;
}

const getCDNEndpoint = () => {
  if (!process.env.DO_STORAGE_CDN_ENDPOINT) {
    throw new Error('DO_STORAGE_CDN_ENDPOINT env variable is not set');
  }
  return process.env.DO_STORAGE_CDN_ENDPOINT;
}

const getBucket = () => {
  if (!process.env.DO_STORAGE_BUCKET) {
    throw new Error('DO_STORAGE_BUCKET env variable is not set');
  }
  return process.env.DO_STORAGE_BUCKET;
}

const getRegion = () => {
  if (!process.env.DO_STORAGE_REGION) {
    throw new Error('DO_STORAGE_REGION env variable is not set');
  }
  return process.env.DO_STORAGE_REGION;
}

export const getSpace = (type: 'origin' | 'cdn') => {
  const _s3 = new S3Client({
    endpoint: type === 'origin' ? getOriginEndpoint() : getCDNEndpoint(),
    region: getRegion(),
    credentials: {
      accessKeyId: process.env.DO_STORAGE_BUCKET_KEY!,
      secretAccessKey: process.env.DO_STORAGE_BUCKET_SECRET!,
    },
  });

  return _s3;
}

export const uploadFile = async ({
  file,
  fileName
}: { file: File, fileName: string }) => {
  const s3Client = getSpace('origin');

  // Convert File to ArrayBuffer, then to Buffer
  const arrayBuffer = await file.arrayBuffer();
  const buffer = Buffer.from(arrayBuffer);

  const params = {
    Bucket: getBucket(),
    Key: fileName,
    Body: buffer,
    ACL: ObjectCannedACL.public_read,
  };

  try {
    const command = new PutObjectCommand(params);
    const response = await s3Client.send(command);

    // Use the existing endpoint for the file URL
    const fileUrl = `${getCDNEndpoint()}/${fileName}`;

    return {
      url: fileUrl,
      response
    };
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};

export const getFileUrl = (fileName: string) => {
  const endpoint = getCDNEndpoint();
  return `${endpoint}/${fileName}`; // Change to your Space URL
};

// Optional: Clean up resources when done
export const closeConnection = () => {
  getSpace('origin').destroy();
  getSpace('cdn').destroy();
};
