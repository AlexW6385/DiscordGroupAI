from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, BigInteger
from sqlalchemy.sql import func
from db.database import Base

class GuildSettings(Base):
    __tablename__ = "guild_settings"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    proactive_mode = Column(Boolean, default=True)
    global_cooldown = Column(Integer, default=60)
    persona = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ChannelSettings(Base):
    __tablename__ = "channel_settings"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(BigInteger, ForeignKey("guild_settings.guild_id"), index=True, nullable=False)
    channel_id = Column(BigInteger, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class MessageRecord(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(BigInteger, unique=True, index=True, nullable=False)
    guild_id = Column(BigInteger, index=True, nullable=False)
    channel_id = Column(BigInteger, index=True, nullable=False)
    user_id = Column(BigInteger, index=True, nullable=False)
    username = Column(String(255), nullable=False)
    raw_content = Column(Text, nullable=False)
    cleaned_content = Column(Text, nullable=False)
    is_bot = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

class BotDecision(Base):
    __tablename__ = "bot_decisions"

    id = Column(Integer, primary_key=True, index=True)
    trigger_message_id = Column(BigInteger, nullable=True) # Message that triggered the decision
    guild_id = Column(BigInteger, nullable=False)
    channel_id = Column(BigInteger, nullable=False)
    should_respond = Column(Boolean, nullable=False)
    priority = Column(Float, nullable=True)
    mode = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    response_content = Column(Text, nullable=True)
    sent_message_id = Column(BigInteger, nullable=True) # Message sent by the bot (if any)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

