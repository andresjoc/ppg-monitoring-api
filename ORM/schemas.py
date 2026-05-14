from pydantic import BaseModel, EmailStr
from decimal import Decimal
from datetime import date, datetime
from typing import Optional


class CountryCreate(BaseModel):
    name: str


class CountryResponse(BaseModel):
    id_country: int
    name: str

    class Config:
        from_attributes = True


class RegionCreate(BaseModel):
    name: str
    id_country: int


class RegionResponse(BaseModel):
    id_region: int
    name: str
    id_country: int

    class Config:
        from_attributes = True


class CityCreate(BaseModel):
    name: str
    id_region: int


class CityResponse(BaseModel):
    id_city: int
    name: str
    id_region: int

    class Config:
        from_attributes = True


class AppUserCreate(BaseModel):
    id_city: int
    email: EmailStr
    first_name: str
    last_name: str
    birth_date: date


class AppUserResponse(BaseModel):
    id_user: int
    id_city: Optional[int] = None
    email: EmailStr
    first_name: str
    last_name: str
    birth_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthRecordCreate(BaseModel):
    weight_kg: float
    height_cm: float


class HealthRecordResponse(BaseModel):
    id_health_record: int
    id_user: int
    weight_kg: float
    height_cm: float
    recorded_at: datetime

    class Config:
        from_attributes = True


class WearableModelCreate(BaseModel):
    brand: str
    model: str


class WearableModelResponse(BaseModel):
    id_wearable_model: int
    brand: str
    model: str

    class Config:
        from_attributes = True


class WearableCreate(BaseModel):
    id_wearable_model: int
    mac_address: str


class WearableResponse(BaseModel):
    id_wearable: int
    id_user: int
    id_wearable_model: int
    mac_address: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MonitoringSessionCreate(BaseModel):
    id_compute_status: int
    date_time: datetime
    is_delta_encoded: bool = False


class MonitoringSessionResponse(BaseModel):
    id_session: int
    id_user: int
    id_compute_status: int
    date_time: datetime
    created_at: datetime
    updated_at: datetime
    is_delta_encoded: bool

    class Config:
        from_attributes = True


class MetricTypeCreate(BaseModel):
    unit: str
    min_value: Decimal
    max_value: Decimal
    is_derived: bool = False
    name: str


class MetricTypeResponse(BaseModel):
    id_metric_type: int
    unit: str
    min_value: Decimal
    max_value: Decimal
    is_derived: bool
    name: str

    class Config:
        from_attributes = True


class MeasurementCreate(BaseModel):
    id_metric_type: int
    id_session: int
    value: Decimal
    error_message: str | None = None


class MeasurementResponse(BaseModel):
    id_measurement: int
    id_metric_type: int
    id_session: int
    value: Optional[Decimal] = None
    error_message: str | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class SeverityLevelCreate(BaseModel):
    name: str
    description: str


class SeverityLevelResponse(BaseModel):
    id_severity_level: int
    name: str
    description: str

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    id_session: int
    id_severity_level: int
    description: str


class AlertResponse(BaseModel):
    id_alert: int
    id_session: int
    id_severity_level: int
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComputeStatusCreate(BaseModel):
    name: str
    description: str


class ComputeStatusResponse(BaseModel):
    id_compute_status: int
    name: str
    description: str

    class Config:
        from_attributes = True


class PpgSampleCreate(BaseModel):
    id_session: int
    ts: int
    green: int
    red: Optional[int] = None
    ir: Optional[int] = None


class PpgSampleResponse(BaseModel):
    id_ppg_sample: int
    id_session: int
    ts: int
    green: int
    red: Optional[int] = None
    ir: Optional[int] = None

    class Config:
        from_attributes = True
