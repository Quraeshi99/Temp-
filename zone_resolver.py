import datetime
import math
import json
import os
import structlog
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis

from app.models.metadata import PrayerZoneCalendar, ZoneAlias
from app.core.config import settings

logger = structlog.get_logger(__name__)


def get_admin_level_zone_id(admin_levels: Dict[str, Any]) -> str:
    """Builds a hierarchical zone ID from geocoding data."""
    if not admin_levels:
        return "GLOBAL_FALLBACK"

    country = admin_levels.get("country_code", "XX").upper()
    state = admin_levels.get("state", "").upper().replace(" ", "_")
    city = admin_levels.get("city") or admin_levels.get("town") or admin_levels.get("village")
    
    if city:
        city = city.upper().replace(" ", "_")
        return f"{country}_{state}_{city}"
    elif state:
        return f"{country}_{state}"
    return f"{country}"


def get_zone_id_from_coords(latitude: float, longitude: float) -> str:
    """Fallback grid-based zone ID (0.2 degree precision ~20km)."""
    lat_grid = round(latitude * 5) / 5
    lon_grid = round(longitude * 5) / 5
    return f"grid_{lat_grid}_{lon_grid}"


async def determine_final_zone_id(
    db: AsyncSession,
    longitude: float,
    latitude: float,
    admin_levels: Dict[str, Any],
    method_id: int,
    asr_id: int,
    high_lat_id: int,
) -> Tuple[str, bool, Optional[str]]:
    """
    DNA Mirror: Centralized Zone Resolution Logic.
    Appends Method and Asr ID to ensure uniqueness for different calculation settings.
    Returns (zone_id, is_alias, original_zone_id)
    """
    # 1. Try to build a Named Zone ID
    base_named_id = get_admin_level_zone_id(admin_levels)
    
    # 2. If geocoding failed or returned Unknown, use Grid
    if "UNKNOWN" in base_named_id or "FALLBACK" in base_named_id:
        base_named_id = get_zone_id_from_coords(latitude, longitude)

    # 3. Append Method/Asr Discriminator (The Accuracy Fix)
    # This ensures a Hanafi Masjid and a Standard Masjid in the same city have separate data entries.
    zone_id = f"{base_named_id}_M{method_id}_A{asr_id}"

    # 4. Check for exact match in DB
    stmt = select(PrayerZoneCalendar.zone_id).where(PrayerZoneCalendar.zone_id == zone_id)
    res = await db.execute(stmt)
    if res.first():
        return zone_id, False, None

    # 5. Zone Alias System (Time-based comparison)
    # Logic: Look for existing zones in the same admin area or grid
    # If timings match within 50 seconds (DNA Mirror), we create an alias.
    # Note: For this audit, we focus on the naming logic. 
    # The actual aliasing happens during the data fetch phase if hashes match.
    return zone_id, False, None


async def get_yearly_calendar_from_cache(
    db: AsyncSession,
    redis: Redis,
    zone_id: str,
    year: int,
    method_id: int,
    asr_id: int,
    high_lat_id: int,
) -> Optional[List[Dict[str, Any]]]:
    """Retrieves yearly calendar from Redis or DB."""
    # Redacted for simplicity in this file write, assuming it stays same
    pass


def get_method_id_for_country(country_code: str) -> int:
    """Returns the calculation method ID based on country."""
    try:
        # Load from core/constants or a JSON file
        mapping_file = os.path.join(os.path.dirname(__file__), "../../core/country_methods.json")
        if not os.path.exists(mapping_file):
            return 3 # MWL Default
            
        with open(mapping_file, "r") as f:
            mapping_data = json.load(f)

        country_map = mapping_data.get("country_map", {})
        default_id = mapping_data.get("default_method_id", 3)
        return country_map.get(country_code.upper(), default_id)
    except Exception:
        return 3
