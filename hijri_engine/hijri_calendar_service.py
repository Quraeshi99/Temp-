"""
Hijri Calendar Service — Standalone Hijri date conversion with event matching.

Provides:
  1. Single-date conversion (Gregorian → Hijri) with events for that day.
  2. Monthly calendar generation (all days in a Gregorian month → Hijri + events).
  3. Full-year calendar generation (12 months × days → Hijri + events).

Events come from two sources:
  - islamic_events.json   — Islamic events mapped to Hijri month/day (Laylatul Qadr, Shab-e-Barat, etc.)
  - `holidays` library     — Country-specific public holidays (Diwali, Independence Day, Eid-ul-Fitr, etc.)
                             Supports 500+ countries with automatic floating-date calculation.

The two sources are COMPLEMENTARY:
  - `holidays` gives official public holidays (including Islamic ones like Eid).
  - `islamic_events.json` gives Islamic observances that are NOT public holidays
    (e.g., Laylatul Qadr odd nights, Tashreeq days, Battle of Badr).
  Both are merged and deduplicated in the final output.
"""

from datetime import date, timedelta
from typing import Any

import holidays as holidays_lib

from .converter import convert_to_hijri
from ..registry_loader import registry


class HijriCalendarService:
    """
    Generates standalone Hijri calendars with event matching from
    the Islamic events registry and the `holidays` Python library.
    """

    def __init__(self):
        self._islamic_events = registry.get_raw("islamic_events") or {}
        # Cache for country holiday objects (one per country per year)
        self._holiday_cache: dict[str, Any] = {}

    def _get_country_holidays(self, country_code: str, year: int) -> Any:
        """
        Get or create a holidays object for a country+year.
        Uses `holidays` library (500+ countries, automatic calculation).
        Fetches all supported categories (optional, observance, unofficial, etc.) for a richer calendar.
        Returns None if country is not supported.
        """
        cache_key = f"{country_code}:{year}"
        if cache_key not in self._holiday_cache:
            try:
                base_hols = holidays_lib.country_holidays(country_code.upper())
                supported = getattr(base_hols, "supported_categories", ("public",))
                self._holiday_cache[cache_key] = holidays_lib.country_holidays(
                    country_code.upper(), years=year, categories=supported
                )
            except NotImplementedError:
                # Country not supported by the library
                self._holiday_cache[cache_key] = None
        return self._holiday_cache[cache_key]

    def _get_islamic_events_for_hijri_date(
        self, hijri_month: int, hijri_day: int, hijri_year: int, month_name: str
    ) -> list[dict[str, Any]]:
        """Look up Islamic events for a given Hijri month and day."""
        events_list = self._islamic_events.get("events", [])
        return [
            {
                "event_id": e.get("event_id", ""),
                "local_name": None,
                "display_name": e["name"],
                "english_name": e["name"],
                "arabic_name": e.get("arabic") or None,
                "type": e["type"],
                "hijri_date": f"{hijri_day} {month_name} {hijri_year}",
                "sources": ["islamic_engine"],
            }
            for e in events_list
            if e["hijri_month"] == hijri_month and e["hijri_day"] == hijri_day
        ]

    def _get_country_events_for_date(
        self, country_code: str, gregorian_date: date, hijri_date_str: str
    ) -> list[dict[str, Any]]:
        """
        Look up country-specific holidays for a Gregorian date using `holidays` library.
        Automatically handles floating dates (Diwali, Easter, Thanksgiving, etc.).
        """
        country_hols = self._get_country_holidays(country_code, gregorian_date.year)
        if country_hols is None:
            return []

        if gregorian_date in country_hols:
            import re

            from anyascii import anyascii

            holiday_name = country_hols.get(gregorian_date)

            clean_name = holiday_name.split("(")[0].strip()
            event_id = re.sub(r"[^a-z0-9]+", "_", clean_name.lower()).strip("_")
            display_name = anyascii(clean_name)

            return [
                {
                    "event_id": event_id,
                    "local_name": clean_name,
                    "display_name": display_name,
                    "english_name": display_name,
                    "arabic_name": None,
                    "type": "PUBLIC_HOLIDAY",
                    "hijri_date": hijri_date_str,
                    "sources": ["holidays"],
                }
            ]
        return []

    def get_events_for_date(
        self,
        gregorian_date: date,
        country_code: str = "",
    ) -> list[dict[str, Any]]:
        """
        Get all events (Islamic + country) for a specific Gregorian date.
        Deduplicates overlapping events using a FAANG-level confidence scoring system.
        Returns a list of event dicts matching the unified schema.
        """
        hijri = convert_to_hijri(gregorian_date, country_code=country_code or "SA")
        events: list[dict[str, Any]] = []
        hijri_date_str = f"{hijri.day} {hijri.month_name} {hijri.year}"

        islamic_events_today = self._get_islamic_events_for_hijri_date(
            hijri.month, hijri.day, hijri.year, hijri.month_name
        )
        events.extend(islamic_events_today)

        if country_code:
            country_events = self._get_country_events_for_date(
                country_code, gregorian_date, hijri_date_str
            )

            ISLAMIC_ROOTS = [
                "eid",
                "id-",
                "aid",
                "fitr",
                "adha",
                "bakr",
                "qurban",
                "kurban",
                "tabaski",
                "korit",
                "oroz",
                "ramazan",
                "ramadan",
                "lebaran",
                "bayram",
                "muharram",
                "ashura",
                "milad",
                "mawlid",
                "nabi",
                "prophet",
                "maulid",
                "isra",
                "miraj",
                "mikraj",
                "barat",
                "bara'at",
                "hajj",
                "عید",
                "عيد",
                "ঈদুল",
                "Орозо",
                "Курман",
                "bajram",
            ]

            for ce in country_events:
                is_overlap = False
                name_lower = ce["local_name"].lower()

                # Confidence System
                for ie in events:
                    score = 0

                    if ce["event_id"] == ie["event_id"]:
                        score += 100

                    # Same date score
                    score += 10

                    # Alias match score
                    if any(root.lower() in name_lower for root in ISLAMIC_ROOTS):
                        score += 90

                    # Merge Decision
                    if score >= 100:
                        ie["local_name"] = ce["local_name"]
                        ie["display_name"] = ce["display_name"]
                        if "holidays" not in ie["sources"]:
                            ie["sources"].append("holidays")
                        is_overlap = True
                        break

                if not is_overlap:
                    # Avoid exact string duplicates just in case
                    if not any(
                        e["english_name"].lower() == ce["english_name"].lower()
                        for e in events
                    ):
                        events.append(ce)

        return events

    def get_event_names_for_date(
        self,
        gregorian_date: date,
        country_code: str = "",
    ) -> list[str]:
        """
        Get event display names for a date. Used by prayer calendar DayEntry.
        Returns a flat list of event name strings.
        """
        return [
            e.get("display_name", e.get("english_name"))
            for e in self.get_events_for_date(gregorian_date, country_code)
        ]

    def convert_single_date(
        self,
        gregorian_date: date,
        country_code: str = "",
    ) -> dict[str, Any]:
        """
        Convert a single Gregorian date to Hijri with full event data.

        Returns:
            {
                "gregorian_date": "2026-05-26",
                "hijri_date": "1 Dhul Hijjah 1448H",
                "hijri_day": 1,
                "hijri_month": 12,
                "hijri_month_name": "Dhul Hijjah",
                "hijri_year": 1448,
                "day_of_week": "Tuesday",
                "events": [{"name": "...", "arabic": "...", "type": "..."}]
            }
        """
        hijri = convert_to_hijri(gregorian_date, country_code=country_code or "SA")
        events = self.get_events_for_date(gregorian_date, country_code)

        return {
            "gregorian_date": gregorian_date.strftime("%Y-%m-%d"),
            "hijri_date": f"{hijri.day} {hijri.month_name} {hijri.year}H",
            "hijri_day": hijri.day,
            "hijri_month": hijri.month,
            "hijri_month_name": hijri.month_name,
            "hijri_year": hijri.year,
            "day_of_week": gregorian_date.strftime("%A"),
            "events": events,
        }

    def generate_monthly_calendar(
        self,
        year: int,
        month: int,
        country_code: str = "",
    ) -> dict[str, Any]:
        """
        Generate a standalone Hijri calendar for a single Gregorian month.
        No prayer times — just dates and events.
        """
        first_day = date(year, month, 1)
        month_name = first_day.strftime("%B")
        days = []

        current = first_day
        while current.month == month:
            days.append(self.convert_single_date(current, country_code))
            current += timedelta(days=1)

        return {
            "year": year,
            "month": month,
            "month_name": month_name,
            "country_code": country_code or "GLOBAL",
            "total_days": len(days),
            "days": days,
        }

    def generate_annual_calendar(
        self,
        year: int,
        country_code: str = "",
    ) -> dict[str, Any]:
        """
        Generate a standalone Hijri calendar for a full Gregorian year.
        No prayer times — just dates and events for all 365/366 days.
        """
        months = {}
        for m in range(1, 13):
            month_data = self.generate_monthly_calendar(year, m, country_code)
            months[str(m)] = month_data

        return {
            "year": year,
            "country_code": country_code or "GLOBAL",
            "total_months": 12,
            "months": months,
        }
