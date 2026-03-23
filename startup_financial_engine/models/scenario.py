from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="scenarios")
    decisions = relationship(
        "ScenarioDecision",
        back_populates="scenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    simulation_runs = relationship(
        "SimulationRun",
        back_populates="scenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )