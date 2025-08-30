"""
Refactored Database models for ARGO NetCDF data using SQLAlchemy ORM
This version normalizes the measurement data for better analytical queries.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class ArgoFloat(Base):
    """Model for ARGO float metadata - unchanged from original"""
    __tablename__ = 'argo_floats'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_number = Column(String(20), unique=True, nullable=False, index=True)
    first_location_lat = Column(Float)
    first_location_lon = Column(Float)
    first_measurement_time = Column(DateTime)
    total_cycles = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profiles = relationship("ArgoProfile", back_populates="float", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ArgoFloat(platform_number='{self.platform_number}', total_cycles={self.total_cycles})>"

class ArgoProfile(Base):
    """
    Model for ARGO profile metadata only - measurements moved to separate table
    """
    __tablename__ = 'argo_profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    float_id = Column(UUID(as_uuid=True), ForeignKey('argo_floats.id'), nullable=False)
    cycle_number = Column(Integer, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    measurement_time = Column(DateTime)
    num_measurements = Column(Integer)  # Keep this for quick reference
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    float = relationship("ArgoFloat", back_populates="profiles")
    measurements = relationship("ArgoMeasurement", back_populates="profile", cascade="all, delete-orphan")
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('float_id', 'cycle_number', name='unique_float_cycle'),)
    
    def __repr__(self):
        return f"<ArgoProfile(platform={self.float.platform_number if self.float else 'Unknown'}, cycle={self.cycle_number})>"

class ArgoMeasurement(Base):
    """
    Model for individual ARGO measurements - normalized structure
    Each row represents one measurement point with pressure, temperature, and salinity
    """
    __tablename__ = 'argo_measurements'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey('argo_profiles.id'), nullable=False)
    measurement_order = Column(Integer, nullable=False)  # Order within the profile (0, 1, 2, ...)
    pressure = Column(Float, nullable=True)  # Can be null if no valid measurement
    temperature = Column(Float, nullable=True)  # Can be null if no valid measurement
    salinity = Column(Float, nullable=True)  # Can be null if no valid measurement
    
    # Relationship
    profile = relationship("ArgoProfile", back_populates="measurements")
    
    # Indexes for analytical queries
    __table_args__ = (
        Index('idx_measurements_profile_order', 'profile_id', 'measurement_order'),
        Index('idx_measurements_pressure', 'pressure'),
        Index('idx_measurements_temperature', 'temperature'),
        Index('idx_measurements_salinity', 'salinity'),
        UniqueConstraint('profile_id', 'measurement_order', name='unique_profile_measurement_order'),
    )
    
    def __repr__(self):
        return f"<ArgoMeasurement(profile_id={self.profile_id}, order={self.measurement_order}, p={self.pressure}, t={self.temperature}, s={self.salinity})>"
