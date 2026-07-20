"""Environmental data collection, adapter, normalization, and seed module."""

from .adapters import (
    EnvironmentalDataAdapter,
    EnvironmentalIngestionService,
    OpenAQReadingsAdapter,
    OpenMeteoWeatherAdapter,
    OpenMeteoWindAdapter,
    SeededEnvironmentalDataAdapter,
)
from .normalization import EnvironmentalDataNormalizer, GeoMasterWardResolver, StationMapping, StaticWardResolver
from .schemas import (
    AirQualityReadingDTO,
    ControlledScenarioDTO,
    EnvironmentalIngestionBatch,
    EnvironmentalNormalizationResult,
    NormalizedAirQualityReading,
    RejectedEnvironmentalRecord,
    WeatherObservationDTO,
    WindObservationDTO,
)

__all__ = [
    "AirQualityReadingDTO",
    "ControlledScenarioDTO",
    "EnvironmentalDataAdapter",
    "EnvironmentalDataNormalizer",
    "EnvironmentalIngestionBatch",
    "EnvironmentalIngestionService",
    "EnvironmentalNormalizationResult",
    "GeoMasterWardResolver",
    "NormalizedAirQualityReading",
    "OpenAQReadingsAdapter",
    "OpenMeteoWeatherAdapter",
    "OpenMeteoWindAdapter",
    "RejectedEnvironmentalRecord",
    "SeededEnvironmentalDataAdapter",
    "StationMapping",
    "StaticWardResolver",
    "WeatherObservationDTO",
    "WindObservationDTO",
]
