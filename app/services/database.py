# # src/app/services/database.py

# """
# WHAT?
# -----
# This file configures the async database engine for PostgreSQL (Supabase)
# using SQLAlchemy.

# WHY?
# ----
# Your entire backend needs:
# - engine → main connection to the DB
# - async_session → to create DB sessions
# - Base → for models to attach their tables
# - get_db() → FastAPI dependency injection

# HOW?
# ----
# Any endpoint can do:
# db: AsyncSession = Depends(get_db)
# """

# from sqlalchemy.ext.asyncio import (
#     AsyncSession,
#     create_async_engine
# )
# from sqlalchemy.orm import sessionmaker, declarative_base

# from app.config import settings

# # Base class for all SQLAlchemy models
# Base = declarative_base()

# # Async engine (Supabase PostgreSQL)
# engine = create_async_engine(
#     settings.database_url,
#     echo=True,             # prints SQL queries (good for debugging)
#     future=True
# )

# # Async session factory
# async_session = sessionmaker(
#     engine,
#     expire_on_commit=False,
#     class_=AsyncSession
# )


# # Dependency for FastAPI endpoints
# async def get_db() -> AsyncSession:
#     async with async_session() as session:
#         yield session
