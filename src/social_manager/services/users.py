from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from social_manager.db.models import User
from social_manager.domain.schemas import UserCreate, UserUpdate
from social_manager.security import hash_password, verify_password


class UserAlreadyExistsError(ValueError):
    pass


class UserService:
    async def create(self, session: AsyncSession, data: UserCreate) -> User:
        existing = await session.scalar(select(User).where(User.email == data.email.lower()))
        if existing is not None:
            raise UserAlreadyExistsError("A user with this email already exists")
        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            display_name=data.display_name,
            timezone=data.timezone,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def authenticate(self, session: AsyncSession, email: str, password: str) -> User | None:
        user = await session.scalar(select(User).where(User.email == email.lower()))
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            return None
        return user

    async def get(self, session: AsyncSession, user_id: str) -> User | None:
        return await session.get(User, user_id)

    async def update(self, session: AsyncSession, user: User, data: UserUpdate) -> User:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(user, key, value)
        await session.commit()
        await session.refresh(user)
        return user
