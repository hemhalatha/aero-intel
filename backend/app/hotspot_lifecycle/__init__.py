"""Hotspot lifecycle persistence and state management for AeroIntel."""

from .schemas import HotspotRecord, HotspotStateUpdate, HotspotStatus
from .service import HotspotLifecycleService

__all__ = ["HotspotLifecycleService", "HotspotRecord", "HotspotStateUpdate", "HotspotStatus"]
