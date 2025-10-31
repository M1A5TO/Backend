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
    Enum,
    Index,
    CHAR,
    event,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import ENUM
from geoalchemy2 import Geography

Base = declarative_base()

# ===============================================
# ENUMY
# ===============================================

source_web_e = ENUM(
    'otodom',
    name='source_web_e',
    create_type=True,
)

poi_desc_e = ENUM(
    'high',
    'medium',
    'low',
    name='poi_desc_e',
    create_type=True,
)

price_desc_e = ENUM(
    'cheap',
    'average',
    'expensive',
    name='price_desc_e',
    create_type=True,
)

size_desc_e = ENUM(
    'small',
    'medium',
    'large',
    name='size_desc_e',
    create_type=True,
)

style_e = ENUM(
    'other',
    name='style_e',
    create_type=True,
)

# ===============================================
# TABELA: apartments
# ===============================================

class Apartment(Base):
    __tablename__ = "apartments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    source_website = Column(source_web_e, nullable=False)
    source_id = Column(String(10), nullable=False)
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

    poi_desc = Column(poi_desc_e)
    price_desc = Column(price_desc_e)
    size_desc = Column(size_desc_e)
    style = Column(style_e)

    photos = relationship("Photo", back_populates="apartment", cascade="all, delete")

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
# TABELA: photos
# ===============================================

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    apartment_id = Column(Integer, ForeignKey("apartments.id", ondelete="CASCADE"), nullable=False)
    path = Column(String(255), nullable=False)

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
        # Do not block DB transaction on filesystem errors
        print(f"[WARN] Failed to remove file {getattr(target, 'path', None)}: {e}")
