import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, func,
    UniqueConstraint, PrimaryKeyConstraint, Index, ForeignKeyConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

class SavedMessage(Base):
    __tablename__ = "saved_messages"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='saved_messages_pkey'),
        UniqueConstraint('user_id', 'message_id', name='saved_messages_user_message_unique'),
        UniqueConstraint('message_id', name='saved_messages_message_id_key'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='saved_messages_user_id_fkey'),
        Index('idx_saved_messages_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    message_id = Column(Text, nullable=False) # Assuming this is related to ConversationMessage.id but SQL uses TEXT UNIQUE, not FK
    conversation_id = Column(Text, nullable=False) # Assuming related to Conversation.id, SQL uses TEXT
    content = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)
    saved_msg_metadata = Column(JSONB, name='metadata', nullable=True) # Renamed attribute
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User") # Simplified
    # Cannot directly link message_id via FK in model if DB uses TEXT UNIQUE
    images = relationship("SavedImage", back_populates="saved_message", cascade="all, delete-orphan")
    videos = relationship("SavedVideo", back_populates="saved_message", cascade="all, delete-orphan")
    songs = relationship("SavedSong", back_populates="saved_message", cascade="all, delete-orphan")

class SavedImage(Base):
    __tablename__ = "saved_images"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='saved_images_pkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='saved_images_user_id_fkey'),
        ForeignKeyConstraint(['message_id'], ['saved_messages.message_id'], name='saved_images_message_id_fkey'),
        Index('idx_saved_images_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    # SQL uses TEXT FK, which isn't standard. Define relationship via back_populates
    message_id = Column(Text, ForeignKey("saved_messages.message_id"), nullable=False)
    image_url = Column(Text, nullable=False)
    prompt = Column(Text, nullable=True)
    saved_img_metadata = Column(JSONB, name='metadata', nullable=True) # Renamed attribute
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User") # Simplified
    saved_message = relationship("SavedMessage", back_populates="images")

class SavedVideo(Base):
    __tablename__ = "saved_videos"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='saved_videos_pkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='saved_videos_user_id_fkey'),
        ForeignKeyConstraint(['message_id'], ['saved_messages.message_id'], name='saved_videos_message_id_fkey'),
        Index('idx_saved_videos_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    message_id = Column(Text, ForeignKey("saved_messages.message_id"), nullable=False)
    video_url = Column(Text, nullable=False)
    prompt = Column(Text, nullable=True)
    saved_vid_metadata = Column(JSONB, name='metadata', nullable=True) # Renamed attribute
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User") # Simplified
    saved_message = relationship("SavedMessage", back_populates="videos")

class SavedSong(Base):
    __tablename__ = "saved_songs"
    __table_args__ = (
        PrimaryKeyConstraint('id', name='saved_songs_pkey'),
        ForeignKeyConstraint(['user_id'], ['users.id'], name='saved_songs_user_id_fkey'),
        ForeignKeyConstraint(['message_id'], ['saved_messages.message_id'], name='saved_songs_message_id_fkey'),
        Index('idx_saved_songs_user', 'user_id'),
    )

    id = Column(PGUUID, primary_key=True, default=uuid4)
    user_id = Column(PGUUID, ForeignKey("users.id"), nullable=False)
    message_id = Column(Text, ForeignKey("saved_messages.message_id"), nullable=False)
    audio_url = Column(Text, nullable=False)
    prompt = Column(Text, nullable=True)
    saved_song_metadata = Column(JSONB, name='metadata', nullable=True) # Renamed attribute
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User") # Simplified
    saved_message = relationship("SavedMessage", back_populates="songs") 