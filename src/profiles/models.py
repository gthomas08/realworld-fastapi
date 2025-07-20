from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, exists
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.users.models import User, user_follows
from src.profiles.service import ProfileService
