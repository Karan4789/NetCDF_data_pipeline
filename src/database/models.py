"""
Database models for ARGO NetCDF data using SQLAlchemy ORM
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class ArgoFloat(Base):
    """Model for ARGO float metadata"""
    __tablename__ = 'argo_floats'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_number = Column(String(20), unique=True, nullable=False, index=True)
    first_location_lat = Column(Float)
    first_location_lon = Column(Float)
    first_measurement_time = Column(DateTime)
    total_cycles = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    profiles = relationship("ArgoProfile", back_populates="float", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ArgoFloat(platform_number='{self.platform_number}', total_cycles={self.total_cycles})>"

class ArgoProfile(Base):
    """Model for ARGO profile data (individual measurements)"""
    __tablename__ = 'argo_profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    float_id = Column(UUID(as_uuid=True), ForeignKey('argo_floats.id'), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    measurement_time = Column(DateTime)
    pressure_values = Column(String)  # JSON string of pressure array
    temperature_values = Column(String)  # JSON string of temperature array
    salinity_values = Column(String)  # JSON string of salinity array
    num_measurements = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    float = relationship("ArgoFloat", back_populates="profiles")
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('float_id', 'cycle_number', name='unique_float_cycle'),)
    
    def __repr__(self):
        return f"<ArgoProfile(platform={self.float.platform_number if self.float else 'Unknown'}, cycle={self.cycle_number})>"

