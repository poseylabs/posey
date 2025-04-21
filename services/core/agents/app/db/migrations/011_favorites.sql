-- Create saved_messages table
CREATE TABLE IF NOT EXISTS saved_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  message_id TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  content TEXT NOT NULL,
  role VARCHAR(50) NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (message_id),
  UNIQUE (user_id, message_id)
);

-- Ensure columns exist before indexing
ALTER TABLE saved_messages ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE saved_messages ADD COLUMN IF NOT EXISTS conversation_id TEXT;

-- Add NOT NULL constraints if needed
ALTER TABLE saved_messages ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE saved_messages ALTER COLUMN message_id SET NOT NULL;
ALTER TABLE saved_messages ALTER COLUMN conversation_id SET NOT NULL;
ALTER TABLE saved_messages ALTER COLUMN content SET NOT NULL;
ALTER TABLE saved_messages ALTER COLUMN role SET NOT NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_saved_messages_user ON saved_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_messages_conversation ON saved_messages(conversation_id);

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
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ensure columns exist before indexing
ALTER TABLE saved_images ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE saved_images ADD COLUMN IF NOT EXISTS message_id TEXT REFERENCES saved_messages(message_id);

-- Add NOT NULL constraints if needed
ALTER TABLE saved_images ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE saved_images ALTER COLUMN message_id SET NOT NULL;
ALTER TABLE saved_images ALTER COLUMN image_url SET NOT NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_saved_images_user ON saved_images(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_images_message ON saved_images(message_id);

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
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ensure columns exist before indexing
ALTER TABLE saved_videos ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE saved_videos ADD COLUMN IF NOT EXISTS message_id TEXT REFERENCES saved_messages(message_id);

-- Add NOT NULL constraints if needed
ALTER TABLE saved_videos ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE saved_videos ALTER COLUMN message_id SET NOT NULL;
ALTER TABLE saved_videos ALTER COLUMN video_url SET NOT NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_saved_videos_user ON saved_videos(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_videos_message ON saved_videos(message_id);

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
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ensure columns exist before indexing
ALTER TABLE saved_songs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);
ALTER TABLE saved_songs ADD COLUMN IF NOT EXISTS message_id TEXT REFERENCES saved_messages(message_id);

-- Add NOT NULL constraints if needed
ALTER TABLE saved_songs ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE saved_songs ALTER COLUMN message_id SET NOT NULL;
ALTER TABLE saved_songs ALTER COLUMN audio_url SET NOT NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_saved_songs_user ON saved_songs(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_songs_message ON saved_songs(message_id);

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
