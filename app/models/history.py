from sqlalchemy import Column, Integer, Float, DateTime
from .base import Base


class History(Base):
    __tablename__ = "histories"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    balance = Column(Float)
    price = Column(Float)
    ratio = Column(Float)
