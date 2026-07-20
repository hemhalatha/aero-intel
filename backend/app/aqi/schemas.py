from pydantic import BaseModel, Field, model_validator


class AQIBandConfig(BaseModel):
    band: str = Field(min_length=1)
    min_value: float = Field(ge=0)
    max_value: float = Field(ge=0)
    severity_rank: int = Field(gt=0)
    display_label: str = Field(min_length=1)
    health_severity_category: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_range(self) -> "AQIBandConfig":
        if self.max_value < self.min_value:
            raise ValueError("max_value must be greater than or equal to min_value")
        return self


class AQIClassification(BaseModel):
    aqi: float
    band: str
    severity_rank: int
    display_label: str
    health_severity_category: str
