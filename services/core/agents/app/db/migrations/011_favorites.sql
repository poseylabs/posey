-- Create saved_messages table
CREATE TABLE IF NOT EXISTS saved_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  message_id TEXT NOT NULL UNIQUE,
  conversation_id TEXT NOT NULL,
  content TEXT NOT NULL,
  role VARCHAR(50) NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add unique constraint explicitly
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'saved_messages_user_message_unique'
    ) THEN
        ALTER TABLE saved_messages 
        ADD CONSTRAINT saved_messages_user_message_unique 
        UNIQUE (user_id, message_id);
    END IF;
END $$;

-- Drop triggers if they exist
DROP TRIGGER IF EXISTS update_saved_messages_updated_at ON saved_messages;

-- Create triggers (without IF NOT EXISTS)
CREATE TRIGGER update_saved_messages_updated_at
    BEFORE UPDATE ON saved_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create saved_images table
CREATE TABLE IF NOT EXISTS saved_images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  message_id TEXT NOT NULL REFERENCES saved_messages(message_id),
  image_url TEXT NOT NULL,
  prompt TEXT,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Drop triggers if they exist
DROP TRIGGER IF EXISTS update_saved_images_updated_at ON saved_images;

-- Create triggers (without IF NOT EXISTS)
CREATE TRIGGER update_saved_images_updated_at
    BEFORE UPDATE ON saved_images
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create saved_videos table
CREATE TABLE IF NOT EXISTS saved_videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  message_id TEXT NOT NULL REFERENCES saved_messages(message_id),
  video_url TEXT NOT NULL,
  prompt TEXT,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Drop triggers if they exist
DROP TRIGGER IF EXISTS update_saved_videos_updated_at ON saved_videos;

-- Create triggers (without IF NOT EXISTS)
CREATE TRIGGER update_saved_videos_updated_at
    BEFORE UPDATE ON saved_videos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create saved_songs table
CREATE TABLE IF NOT EXISTS saved_songs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  message_id TEXT NOT NULL REFERENCES saved_messages(message_id),
  audio_url TEXT NOT NULL,
  prompt TEXT,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Drop triggers if they exist
DROP TRIGGER IF EXISTS update_saved_songs_updated_at ON saved_songs;

-- Create triggers (without IF NOT EXISTS)
CREATE TRIGGER update_saved_songs_updated_at
    BEFORE UPDATE ON saved_songs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_saved_messages_user ON saved_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_images_user ON saved_images(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_videos_user ON saved_videos(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_songs_user ON saved_songs(user_id); 
