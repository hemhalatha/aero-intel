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
from .time_series import EnvironmentalTimeSeriesService
from .time_series_repository import EnvironmentalTimeSeriesRepository
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
from .time_series_schemas import (
    HistoricalBaseline,
    PollutantReading,
    StationLatestState,
    WeatherForecastReading,
    WeatherReading,
    WindReading,
)

__all__ = [
    "AirQualityReadingDTO",
    "ControlledScenarioDTO",
    "EnvironmentalDataAdapter",
    "EnvironmentalDataNormalizer",
    "EnvironmentalIngestionBatch",
    "EnvironmentalIngestionService",
    "EnvironmentalNormalizationResult",
    "EnvironmentalTimeSeriesRepository",
    "EnvironmentalTimeSeriesService",
    "GeoMasterWardResolver",
    "HistoricalBaseline",
    "NormalizedAirQualityReading",
    "OpenAQReadingsAdapter",
    "PollutantReading",
    "OpenMeteoWeatherAdapter",
    "OpenMeteoWindAdapter",
    "RejectedEnvironmentalRecord",
    "SeededEnvironmentalDataAdapter",
    "StationLatestState",
    "StationMapping",
    "StaticWardResolver",
    "WeatherForecastReading",
    "WeatherObservationDTO",
    "WeatherReading",
    "WindObservationDTO",
    "WindReading",
]
