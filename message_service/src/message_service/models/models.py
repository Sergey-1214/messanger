
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func, text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from message_service.db.db import Base

class ChatType(Enum):
    PRIVATE = 1
    GROUP = 2

class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[int] = mapped_column(primary_key=True)

    type: Mapped[ChatType] = mapped_column(
        SQLEnum(
            ChatType,
            name="chat_type",
        ), 
        nullable=False
    )
    is_private: Mapped[bool] = mapped_column(default=True)

    title: Mapped[str | None] = mapped_column(String(250))

    last_message_seq: Mapped[int] = mapped_column(
        BigInteger, 
        nullable=False,
        server_default=text("0"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat",
        passive_deletes=True,
    )

    chat_participants: Mapped[list["ChatParticipant"]] = relationship(
        back_populates="chat",
        passive_deletes=True,
    )


class ChatParticipant(Base):
    __tablename__ = "chats_participant"

    chat_id: Mapped[int] = mapped_column(
        ForeignKey(
            "chats.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    participant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    last_read_seq: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=text("0"),
    )

    chat: Mapped["Chat"] = relationship(
        back_populates="chat_participants",
    )

class Message(Base):
    __tablename__ = "messages"

    __table_args__ = (
        UniqueConstraint("chat_id", "seq", name="uq_seq_chat_id_constraint"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    chat_id: Mapped[int] = mapped_column(
        ForeignKey(
            "chats.id",
            ondelete="CASCADE",
        ), 
        
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    is_deleted: Mapped[bool] = mapped_column(default=False)

    seq: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        server_default=func.now(),
    )

    chat: Mapped["Chat"] = relationship(
        back_populates="messages",
    )