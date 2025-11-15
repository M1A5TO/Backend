import threading
import requests
import os
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    SmallInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    CHAR,
    event,
    Enum as SQLEnum
)
from sqlalchemy.orm import relationship, declarative_base
from enum import Enum as PyEnum
from geoalchemy2 import Geography

Base = declarative_base()

# ===============================================
# ENUMS
# ===============================================

class SourceWeb(PyEnum):
    """Źródła danych o mieszkaniach"""
    OTODOM = "otodom"
    OLX = "olx"
    GRATKA = "gratka"
    MORIZON = "morizon"


class POIAccessibility(PyEnum):
    """Poziom dostępności POI"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PriceCategory(PyEnum):
    """Kategoria cenowa mieszkania"""
    CHEAP = "cheap"
    AVERAGE = "average"
    EXPENSIVE = "expensive"


class SizeCategory(PyEnum):
    """Rozmiar mieszkania"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ApartmentStyle(PyEnum):
    """Styl wykończenia mieszkania"""
    MODERN = "modern"
    CLASSIC = "classic"
    INDUSTRIAL = "industrial"
    SCANDINAVIAN = "scandinavian"
    MINIMALIST = "minimalist"
    VINTAGE = "vintage"
    OTHER = "other"


class POICategory(PyEnum):
    """Kategorie punktów użyteczności publicznej"""
    EDUCATION = "education"
    SHOPPING = "shopping"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    PUBLIC_TRANSPORT = "public_transport"
    FOOD_BEVERAGES = "food_beverages"
    SPORT = "sport"
    PARK = "park"
    SERVICES = "services"

# ===============================================
# TABLE: apartments
# ===============================================

class Apartment(Base):
    __tablename__ = "apartments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    source_website = Column(String(16), nullable=False)
    source_id = Column(String(20), nullable=False)
    source_url = Column(String(255), nullable=False)

    price = Column(Numeric(10, 2))
    currency = Column(CHAR(3), default='PLN')

    room_num = Column(SmallInteger)
    footage = Column(Numeric(6, 2))
    price_per_m2 = Column(Numeric(10, 2))

    city = Column(String(100))
    geolocation = Column(Geography(geometry_type='POINT', srid=4326))

    description = Column(Text)

    photo_attractiveness = Column(SmallInteger)
    student_attractiveness = Column(SmallInteger)
    single_attractiveness = Column(SmallInteger)
    dog_owner_attractiveness = Column(SmallInteger)
    universal_attractiveness = Column(SmallInteger)
    family_attractiveness = Column(SmallInteger)

    poi_desc = Column(SQLEnum(POIAccessibility, name="poi_desc_e"))
    price_desc = Column(SQLEnum(PriceCategory, name="price_desc_e"))
    size_desc = Column(SQLEnum(SizeCategory, name="size_desc_e"))
    # style moved to Photo table

    photos = relationship("Photo", back_populates="apartment", cascade="all, delete")
    pois = relationship("ApartmentPOI", back_populates="apartment", cascade="all, delete")

    __table_args__ = (
        # CHECK constraints
        CheckConstraint('photo_attractiveness BETWEEN 0 AND 100', name='photo_attr_check'),
        CheckConstraint('student_attractiveness BETWEEN 0 AND 100', name='student_attr_check'),
        CheckConstraint('single_attractiveness BETWEEN 0 AND 100', name='single_attr_check'),
        CheckConstraint('dog_owner_attractiveness BETWEEN 0 AND 100', name='dog_owner_attr_check'),
        CheckConstraint('universal_attractiveness BETWEEN 0 AND 100', name='universal_attr_check'),
        CheckConstraint('family_attractiveness BETWEEN 0 AND 100', name='family_attr_check'),
        Index('idx_apartments_city', 'city'),
        Index('idx_apartments_source_id', 'source_website', 'source_id', unique=True),
    )

# ===============================================
# TABLE: photos
# ===============================================

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    apartment_id = Column(Integer, ForeignKey("apartments.id", ondelete="CASCADE"), nullable=False)
    path = Column(String(255), nullable=False)
    style = Column(SQLEnum(ApartmentStyle, name="style_e"))

    apartment = relationship("Apartment", back_populates="photos")

    __table_args__ = (
        Index('idx_photos_apartment_id', 'apartment_id'),
    )

@event.listens_for(Photo, "after_delete")
def after_delete_photo(mapper, connection, target):
    """Remove photo file from disk when record is deleted."""
    try:
        file_path = getattr(target, "path", None)
        if file_path and os.path.isfile(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"[WARN] Failed to remove file {getattr(target, 'path', None)}: {e}")

# ===============================================
# TABLE: POIs
# ===============================================

class POI(Base):
    __tablename__ = "pois"

    id = Column(Integer, primary_key=True, autoincrement=True)
    geolocation = Column(Geography(geometry_type='POINT', srid=4326), nullable=False)
    category = Column(SQLEnum(POICategory, name="poi_category_e"), nullable=False)
    name = Column(String(50), nullable=False)

    apartments = relationship("ApartmentPOI", back_populates="poi", cascade="all, delete")

class ApartmentPOI(Base):
    __tablename__ = "apartment_best_poi"

    apartment_id = Column(Integer, ForeignKey("apartments.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    poi_id = Column(Integer, ForeignKey("pois.id", ondelete="CASCADE"), nullable=False, primary_key=True)
    category = Column(SQLEnum(POICategory, name="poi_category_e"), nullable=False)

    __table_args__ = (
        Index('ix_apartment_best_poi_poi_id', 'poi_id'),
    )

    # Relationships
    apartment = relationship("Apartment", back_populates="pois")
    poi = relationship("POI", back_populates="apartments")
