import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Base
from sqlalchemy import Column, String, Boolean, DateTime, Text, UUID
from datetime import datetime
import uuid

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    archived = Column(Boolean, default=False, nullable=False)
    created = Column(DateTime, default=datetime.now, nullable=False)
    email = Column(String(255), nullable=False)
    fullname = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)
    message = Column(Text, nullable=False)
    subject = Column(String(255), nullable=False)
    viewed = Column(Boolean, default=False, nullable=False)

class Entry(Base):
    __tablename__ = "entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_info = Column(String(255), nullable=False)
    display_info = Column(String(255), nullable=False)
    system_info = Column(String(255), nullable=False)
    browser_info = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)
    created = Column(DateTime, default=datetime.now, nullable=False)

class AdminToken(Base):
    __tablename__ = "admin_token"
    token_hash = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.now, nullable=False)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class Webhook(Base):
    __tablename__ = "webhooks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created = Column(DateTime, default=datetime.now, nullable=False)
    url = Column(String(255), nullable=False)

