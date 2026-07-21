from .schemas import FingerprintPatternConfig, FingerprintPatternRule, FingerprintSource

DEFAULT_FINGERPRINT_PATTERNS = [
    FingerprintPatternConfig(
        source=FingerprintSource.CONSTRUCTION_DUST,
        description="Coarse particulate spike with nearby active construction and supportive wind context.",
        rules=[
            FingerprintPatternRule(feature_name="pm10_pm25_ratio", weight=0.24, min_value=2.0),
            FingerprintPatternRule(feature_name="construction_proximity", weight=0.28, max_value=500),
            FingerprintPatternRule(feature_name="wind_alignment", weight=0.16, expected_bool=True),
            FingerprintPatternRule(feature_name="traffic_anomaly", weight=0.12, max_value=20),
            FingerprintPatternRule(feature_name="so2_level", weight=0.08, max_value=60),
            FingerprintPatternRule(feature_name="temporal_persistence", weight=0.12, min_value=0.4),
        ],
    ),
    FingerprintPatternConfig(
        source=FingerprintSource.VEHICULAR_EMISSIONS,
        description="NO2/CO enrichment with traffic anomaly and rush-hour alignment.",
        rules=[
            FingerprintPatternRule(feature_name="no2_level", weight=0.24, min_value=80),
            FingerprintPatternRule(feature_name="co_level", weight=0.2, min_value=3),
            FingerprintPatternRule(feature_name="traffic_anomaly", weight=0.28, min_value=30),
            FingerprintPatternRule(feature_name="rush_hour_correlation", weight=0.16, expected_bool=True),
            FingerprintPatternRule(feature_name="industrial_proximity", weight=0.06, min_value=1000),
            FingerprintPatternRule(feature_name="construction_proximity", weight=0.06, min_value=700),
        ],
    ),
    FingerprintPatternConfig(
        source=FingerprintSource.INDUSTRIAL_EMISSIONS,
        description="SO2/NO2/CO enrichment near industrial activity with upwind support.",
        rules=[
            FingerprintPatternRule(feature_name="so2_level", weight=0.28, min_value=80),
            FingerprintPatternRule(feature_name="industrial_proximity", weight=0.24, max_value=1000),
            FingerprintPatternRule(feature_name="wind_alignment", weight=0.18, expected_bool=True),
            FingerprintPatternRule(feature_name="no2_level", weight=0.12, min_value=80),
            FingerprintPatternRule(feature_name="co_level", weight=0.1, min_value=3),
            FingerprintPatternRule(feature_name="traffic_anomaly", weight=0.08, max_value=30),
        ],
    ),
    FingerprintPatternConfig(
        source=FingerprintSource.ROAD_DUST,
        description="Coarse particulate dominance with road activity but weaker combustion gases.",
        rules=[
            FingerprintPatternRule(feature_name="pm10_pm25_ratio", weight=0.3, min_value=2.0),
            FingerprintPatternRule(feature_name="traffic_anomaly", weight=0.18, min_value=20),
            FingerprintPatternRule(feature_name="construction_proximity", weight=0.12, min_value=700),
            FingerprintPatternRule(feature_name="no2_level", weight=0.14, max_value=90),
            FingerprintPatternRule(feature_name="so2_level", weight=0.1, max_value=60),
            FingerprintPatternRule(feature_name="temporal_persistence", weight=0.16, min_value=0.4),
        ],
    ),
    FingerprintPatternConfig(
        source=FingerprintSource.BIOMASS_WASTE_BURNING,
        description="Fine particulate and CO enrichment without strong traffic, construction, or industrial evidence.",
        rules=[
            FingerprintPatternRule(feature_name="pm10_pm25_ratio", weight=0.16, max_value=1.8),
            FingerprintPatternRule(feature_name="co_level", weight=0.24, min_value=3),
            FingerprintPatternRule(feature_name="so2_level", weight=0.1, max_value=60),
            FingerprintPatternRule(feature_name="traffic_anomaly", weight=0.14, max_value=20),
            FingerprintPatternRule(feature_name="construction_proximity", weight=0.12, min_value=800),
            FingerprintPatternRule(feature_name="industrial_proximity", weight=0.12, min_value=1200),
            FingerprintPatternRule(feature_name="biomass_burning_marker", weight=0.12, expected_bool=True, missing_penalty=0.1),
        ],
    ),
]
