from app.config import logger
from app.config.settings import settings
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions
from couchbase.cluster import Cluster
from couchbase.management.buckets import CreateBucketSettings, BucketType
from couchbase.exceptions import BucketNotFoundException

async def setup_couchbase():
    """Set up Couchbase collections and indexes"""
    try:
        logger.info("Setting up Couchbase...")
        
        # Get settings
        url = settings.COUCHBASE_URL
        user = settings.COUCHBASE_USER
        password = settings.COUCHBASE_PASSWORD
        bucket = settings.COUCHBASE_BUCKET
        
        if not all([url, user, password, bucket]):
            logger.warning("Skipping Couchbase setup - missing configuration")
            return

        # Initialize cluster connection
        auth = PasswordAuthenticator(user, password)
        cluster = Cluster(url, ClusterOptions(auth))
        
        # Create bucket with proper settings if it doesn't exist
        bucket_manager = cluster.buckets()
        
        # First check if bucket exists by trying to get it
        try:
            bucket = cluster.bucket(bucket)
            logger.info(f"Connected to existing bucket: {bucket}")
        except BucketNotFoundException:
            # Bucket doesn't exist, create it
            try:
                bucket_settings = CreateBucketSettings(
                    name=bucket,
                    bucket_type=BucketType.COUCHBASE,
                    ram_quota_mb=256,  # Minimum RAM quota
                    flush_enabled=True,
                    replica_number=0,  # No replicas for development
                )
                bucket_manager.create_bucket(bucket_settings)
                logger.info(f"Created new Couchbase bucket: {bucket}")
                
                # Wait a moment for the bucket to be ready
                import time
                time.sleep(2)
                
                # Now get the bucket
                bucket = cluster.bucket(bucket)
            except Exception as e:
                logger.error(f"Failed to create bucket: {e}")
                raise

        # Get collection reference
        collection = bucket.default_collection()
        
        # Create indexes
        queries = [
            "CREATE PRIMARY INDEX ON `{}` IF NOT EXISTS",
            "CREATE INDEX idx_agent_type ON `{}`(type) IF NOT EXISTS",
            "CREATE INDEX idx_agent_capabilities ON `{}`(ALL ARRAY c FOR c IN capabilities END) IF NOT EXISTS"
        ]
        
        for query in queries:
            try:
                cluster.query(query.format(bucket))
                logger.info(f"Created/verified index: {query}")
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f"Index already exists: {query}")
                else:
                    logger.error(f"Error creating index: {e}")

        logger.info("Couchbase setup complete")
        
    except Exception as e:
        logger.error(f"Error setting up Couchbase: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_couchbase())
