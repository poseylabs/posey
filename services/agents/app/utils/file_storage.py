import os
import boto3
from botocore.exceptions import ClientError
import asyncio
import aiohttp
from typing import Literal

def get_origin_endpoint() -> str:
    endpoint = os.environ.get("DO_STORAGE_ORIGIN_ENDPOINT")
    if not endpoint:
        raise ValueError("DO_STORAGE_ORIGIN_ENDPOINT env variable is not set")
    return endpoint

def get_cdn_endpoint() -> str:
    endpoint = os.environ.get("DO_STORAGE_CDN_ENDPOINT")
    if not endpoint:
        raise ValueError("DO_STORAGE_CDN_ENDPOINT env variable is not set")
    return endpoint

def get_bucket() -> str:
    bucket = os.environ.get("DO_STORAGE_BUCKET")
    if not bucket:
        raise ValueError("DO_STORAGE_BUCKET env variable is not set")
    return bucket

def get_region() -> str:
    region = os.environ.get("DO_STORAGE_REGION")
    if not region:
        raise ValueError("DO_STORAGE_REGION env variable is not set")
    return region

def get_s3_client(endpoint_type: Literal['origin', 'cdn'] = 'origin'):
    """
    Return an S3 client configured for DigitalOcean Spaces.
    """
    endpoint = get_cdn_endpoint() if endpoint_type == 'cdn' else get_origin_endpoint()
    
    return boto3.client(
        "s3",
        region_name=get_region(),
        endpoint_url=endpoint,
        aws_access_key_id=os.environ.get("DO_STORAGE_BUCKET_KEY"),
        aws_secret_access_key=os.environ.get("DO_STORAGE_BUCKET_SECRET"),
    )

def get_file_url(key: str, endpoint_type: Literal['origin', 'cdn'] = 'cdn') -> str:
    """Get the public URL for a file"""
    endpoint = get_cdn_endpoint() if endpoint_type == 'cdn' else get_origin_endpoint()
    return f"{endpoint}/{key}"

def upload_file(file_bytes: bytes, user_id: str, agent_id: str, file_name: str) -> str:
    """
    Upload file_bytes to the DigitalOcean Spaces bucket under a directory structure based on user_id and agent_id.
    
    :param file_bytes: The binary content of the image.
    :param user_id: The unique identifier for the user.
    :param agent_id: The unique identifier for the agent.
    :param file_name: The name to save the file as.
    :return: A public URL of the uploaded file.
    """
    s3 = get_s3_client('origin')
    bucket = get_bucket()

    # Use a directory structure: {user_id}/{agent_id}/{file_name}
    key = f"{user_id}/{agent_id}/{file_name}"

    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=file_bytes,
            ACL="public-read"
        )
        # Return CDN URL for public access
        return get_file_url(key, 'cdn')
    except ClientError as e:
        raise e

async def copy_generated_image(generated_url: str, user_id: str, agent_id: str, file_name: str) -> str:
    """
    Downloads the image from the given generated_url and uploads it to the DO storage bucket.
    
    :param generated_url: The temporary URL returned by the image generation service.
    :param user_id: The unique identifier for the user.
    :param agent_id: The unique identifier for the agent.
    :param file_name: The filename to be used in the bucket.
    :return: The public URL of the uploaded image.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(generated_url) as response:
            if response.status != 200:
                raise ValueError(f"Failed to download image from {generated_url}, status: {response.status}")
            file_bytes = await response.read()

    # Run the synchronous upload function in a thread
    file_url = await asyncio.to_thread(upload_file, file_bytes, user_id, agent_id, file_name)
    return file_url 
