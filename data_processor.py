import datetime
import json
import hashlib
import structlog
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.metadata import PrayerZoneCalendar, HijriDateOracle
from app.services.prayer_time.ume.engine import calculate_month
from app.services.prayer_time.ume.method_mapper import MethodMapper

logger = structlog.get_logger(__name__)


class DataProcessor:
    @staticmethod
    async def get_yearly_calendar_data(
        db: AsyncSession,
        zone_id: str,
        year: int,
        method_id: int,
        asr_juristic_id: int,
        high_latitude_method_id: int,
        latitude: float,
        longitude: float,
        force_refresh: bool = False,
        country_code: str = "IN",
    ) -> Optional[List]:
        """
        Calculates, hashes, and upserts yearly prayer data using UME engine.
        No external API calls — all calculation happens locally.

        WORKING PRESERVED:
        - Same function signature (+ country_code param with default)
        - Same DB operations (HijriDateOracle + PrayerZoneCalendar upsert)
        - Same hash-based version detection
        - Same return format for downstream consumers
        """
        composite_method_key = (
            f"{method_id}-{asr_juristic_id}-{high_latitude_method_id}"
        )

        # 1. Convert integer IDs to UME string IDs
        ume_method = MethodMapper.method_int_to_str(method_id)
        ume_madhab = MethodMapper.madhab_int_to_str(asr_juristic_id)

        # 2. Calculate yearly data using UME engine (LOCAL — no API call)
        yearly_data = []
        for month in range(1, 13):
            try:
                month_data = calculate_month(
                    year=year,
                    month=month,
                    lat=latitude,
                    lon=longitude,
                    country_code=country_code,
                    method_id=ume_method,
                    madhab_id=ume_madhab,
                )
                yearly_data.extend(month_data)
            except Exception as e:
                logger.error(
                    "ume_month_calc_failed",
                    month=month, year=year, error=str(e)
                )

        if not yearly_data:
            logger.error("ume_yearly_calc_empty", zone=zone_id, year=year)
            return None

        # 3. Populate HijriDateOracle (same DB logic as before)
        try:
            for day_data in yearly_data:
                g_date_str = day_data.get("date")  # "2026-06-14" (ISO)
                h_detail = day_data.get("hijri_detail", {})

                if not g_date_str or not h_detail:
                    continue

                g_date = datetime.datetime.strptime(g_date_str, "%Y-%m-%d").date()
                h_str = f"{h_detail.get('day')} {h_detail.get('month_name')} {h_detail.get('year')}"

                stmt_h = select(HijriDateOracle).where(
                    HijriDateOracle.gregorian_date == g_date,
                    HijriDateOracle.region_key == zone_id,
                    HijriDateOracle.fiqh_key == "global",
                )
                res_h = await db.execute(stmt_h)
                existing_h = res_h.scalar_one_or_none()

                if existing_h:
                    if existing_h.hijri_date_str != h_str:
                        existing_h.hijri_day = int(h_detail.get("day"))
                        existing_h.hijri_month = int(h_detail.get("month"))
                        existing_h.hijri_year = int(h_detail.get("year"))
                        existing_h.hijri_date_str = h_str
                        existing_h.version += 1
                else:
                    new_h = HijriDateOracle(
                        gregorian_date=g_date,
                        region_key=zone_id,
                        fiqh_key="global",
                        hijri_day=int(h_detail.get("day")),
                        hijri_month=int(h_detail.get("month")),
                        hijri_year=int(h_detail.get("year")),
                        hijri_date_str=h_str,
                        source="ume_engine_v1",
                        version=1,
                    )
                    db.add(new_h)

            logger.info("hijri_oracle_prepared", count=len(yearly_data))
        except Exception as e:
            logger.error("hijri_oracle_failed", error=str(e))

        # 4. Hash Calculation (same logic)
        calendar_data_str = json.dumps(
            yearly_data, sort_keys=True, separators=(",", ":")
        )
        calendar_hash = hashlib.sha256(calendar_data_str.encode("utf-8")).hexdigest()

        # 5. Upsert PrayerZoneCalendar (same DB logic)
        try:
            stmt = select(PrayerZoneCalendar).where(
                PrayerZoneCalendar.zone_id == zone_id,
                PrayerZoneCalendar.year == year,
                PrayerZoneCalendar.calculation_method == composite_method_key,
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                if existing.calendar_hash != calendar_hash:
                    existing.calendar_data = yearly_data
                    existing.calendar_hash = calendar_hash
                    existing.version += 1
                    existing.updated_at = datetime.datetime.utcnow()
            else:
                new_calendar = PrayerZoneCalendar(
                    zone_id=zone_id,
                    year=year,
                    calculation_method=composite_method_key,
                    calendar_data=yearly_data,
                    calendar_hash=calendar_hash,
                    version=1,
                    schema_version="v1",
                )
                db.add(new_calendar)

            await db.commit()
            return yearly_data
        except Exception as e:
            await db.rollback()
            logger.error("calendar_upsert_failed", error=str(e))
            return None
