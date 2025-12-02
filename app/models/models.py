# # app/models/models.py

# from sqlalchemy import Column, Integer, String, Text, DateTime
# from sqlalchemy.sql import func
# from app.services.database import Base

# """
# This file defines all database tables using SQLAlchemy ORM.
# Right now we only need one table: Article.
# """


# class Article(Base):
#     __tablename__ = "articles"

#     id = Column(Integer, primary_key=True, index=True)

#     url = Column(String(500), nullable=False, unique=True)
#     title = Column(String(500), nullable=True)
#     summary = Column(Text, nullable=True)
#     full_text = Column(Text, nullable=True)
#     raw_html = Column(Text, nullable=True)
#     source = Column(String(200), nullable=True)

#     # Auto timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
