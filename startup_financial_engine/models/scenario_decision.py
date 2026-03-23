from sqlalchemy import Column, DateTime, ForeignKey, Float, Integer, String, func

from sqlalchemy.orm import relationship
from database import Base


class ScenarioDecision(Base):
    __tablename__ = "scenario_decisions"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)

    type = Column(String, nullable=False)
    name = Column(String, nullable=False)

    impact = Column(Float, nullable=False)

    start_month = Column(Integer, nullable=False)
    lag_months = Column(Integer, nullable=False, server_default="0")
    ramp_months = Column(Integer, nullable=False, server_default="1")

    # NULL => permanent
    duration_months = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    scenario = relationship("Scenario", back_populates="decisions")