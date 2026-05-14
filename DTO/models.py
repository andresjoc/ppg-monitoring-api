#sqlalchemy
from sqlalchemy import DECIMAL, BigInteger, Boolean, Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from DAO.database import Base

class Country(Base):
    __tablename__ = "country"

    id_country = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)


class Region(Base):
    __tablename__ = "region"

    id_region = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_country = Column(Integer, ForeignKey("country.id_country"), nullable=False)
    name = Column(String(100), nullable=False)

    country = relationship("Country")
    cities = relationship("City", back_populates="region")


class City(Base):
    __tablename__ = "city"

    id_city = Column(Integer, primary_key=True, index=True)
    id_region = Column(Integer, ForeignKey("region.id_region"), nullable=False)
    name = Column(String(100), nullable=False)

    users = relationship("App_user", back_populates="city")
    region = relationship("Region", back_populates="cities")


class App_user(Base):
    __tablename__ = "app_user"

    id_user = Column(Integer, primary_key=True, index=True)
    id_city = Column(Integer, ForeignKey("city.id_city"), nullable=True)

    email = Column(String(50), unique=True, nullable=False, index=True)

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    birth_date = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

   
    city = relationship("City", back_populates="users")
    health_records = relationship(
        "HealthRecord",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    wearables = relationship("Wearable", back_populates="user")

    monitoring_sessions = relationship(
    "MonitoringSession",
    back_populates="user"
)


class HealthRecord(Base):
    __tablename__ = "health_record"

    id_health_record = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("app_user.id_user"), nullable=False)

    weight_kg = Column(DECIMAL(5, 2), nullable=False)
    height_cm = Column(DECIMAL(5, 1), nullable=False)
    recorded_at = Column(DateTime, server_default=func.now())

    user = relationship("App_user", back_populates="health_records")


class WearableModel(Base):
    __tablename__ = "wearable_model"

    id_wearable_model = Column(Integer, primary_key=True, index=True)
    brand = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)

    # Relación con Wearable (1 a muchos)
    wearables = relationship(
        "Wearable",
        back_populates="wearable_model",
        cascade="all, delete-orphan"
    )

class Wearable(Base):
    __tablename__ = "wearable"

    id_wearable = Column(Integer, primary_key=True, index=True)
    id_wearable_model = Column(Integer, ForeignKey("wearable_model.id_wearable_model"), nullable=False)
    id_user = Column(Integer, ForeignKey("app_user.id_user"), nullable=False)

    mac_address = Column(String(100), unique=True, nullable=False)

    wearable_model = relationship("WearableModel", back_populates="wearables")
    user = relationship("App_user", back_populates="wearables")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class MonitoringSession(Base):
    __tablename__ = "monitoring_session"

    id_session = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("app_user.id_user"), nullable=False)
    id_compute_status = Column(
    BigInteger,
    ForeignKey("compute_status.id_compute_status"),
    nullable=False)   

    date_time = Column(DateTime, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    is_delta_encoded = Column(Boolean, nullable=False, default=False)

    user = relationship("App_user", back_populates="monitoring_sessions")

    measurements = relationship(
        "Measurement",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    alerts = relationship(
        "Alert",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    compute_status = relationship("ComputeStatus", back_populates="sessions")

    ppg_samples = relationship(
    "PpgSample",
    back_populates="session",
    cascade="all, delete-orphan")

    user = relationship("App_user", back_populates="monitoring_sessions")


class MetricType(Base):
    __tablename__ = "metric_type"

    id_metric_type = Column(Integer, primary_key=True, index=True)

    unit = Column(String(20), nullable=False)
    min_value = Column(DECIMAL(5, 2), nullable=False)
    max_value = Column(DECIMAL(5, 2), nullable=False)
    is_derived = Column(Boolean, nullable=False, default=False)
    name = Column(String(255), unique=True, nullable=False, index=True)

    measurements = relationship("Measurement", back_populates="metric_type")


class Measurement(Base):
    __tablename__ = "measurement"

    id_measurement = Column(Integer, primary_key=True, index=True)

    id_metric_type = Column(
        Integer,
        ForeignKey("metric_type.id_metric_type"),
        nullable=False
    )

    id_session = Column(
        Integer,
        ForeignKey("monitoring_session.id_session"),
        nullable=False
    )

    value = Column(DECIMAL(10, 4), nullable=False)
    error_message = Column(String(255), nullable=True)
    recorded_at = Column(DateTime, server_default=func.now())

    metric_type = relationship("MetricType", back_populates="measurements")
    session = relationship("MonitoringSession", back_populates="measurements")



class SeverityLevel(Base):
    __tablename__ = "severity_level"

    id_severity_level = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    name = Column(String(255), unique=True, nullable=False, index=True)

    alerts = relationship("Alert", back_populates="severity_level")


class Alert(Base):
    __tablename__ = "alert"

    id_alert = Column(Integer, primary_key=True, index=True)

    id_session = Column(Integer, ForeignKey("monitoring_session.id_session"), nullable=False)
    id_severity_level = Column(Integer, ForeignKey("severity_level.id_severity_level"), nullable=False)

    description = Column(String(255), nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    session = relationship("MonitoringSession", back_populates="alerts")
    severity_level = relationship("SeverityLevel", back_populates="alerts")

class ComputeStatus(Base):
    __tablename__ = "compute_status"

    id_compute_status = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)

    sessions = relationship("MonitoringSession", back_populates="compute_status")

class PpgSample(Base):
    __tablename__ = "ppg_sample"

    id_ppg_sample = Column(BigInteger, primary_key=True, index=True)
    id_session = Column(Integer, ForeignKey("monitoring_session.id_session"), nullable=False)

    ts = Column(BigInteger, nullable=False)
    green = Column(Integer, nullable=False)
    red = Column(Integer, nullable=True)
    ir = Column(Integer, nullable=True)

    session = relationship("MonitoringSession", back_populates="ppg_samples")
