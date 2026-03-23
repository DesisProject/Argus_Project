from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    scenarios = relationship(
        "Scenario",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    simulation_runs = relationship(
        "SimulationRun",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )