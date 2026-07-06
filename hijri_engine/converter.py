from datetime import date, timedelta

from hijri_converter import Gregorian

from .regional_adjustment import get_regional_offset


class HijriDateResponse:
    """
    Data model for the Hijri Date return object.
    Industry Standard format.
    """

    def __init__(self, day: int, month: int, year: int, month_name: str):
        self.day = day
        self.month = month
        self.year = year
        self.month_name = month_name


def convert_to_hijri(
    gregorian_date: date, country_code: str = "SA"
) -> HijriDateResponse:
    """
    Converts a Gregorian date to Hijri using the Umm al-Qura calendar system,
    with dynamic regional adjustments for local moon-sighting.

    Args:
        gregorian_date: The standard date to convert.
        country_code: ISO 2-letter country code (e.g., IN, PK, SA).

    RATIONALE:
    While full algorithmic moon-sighting (Yallop/Danjon) requires tracing lunar
    phases back to a known epoch for a specific longitude/latitude, the Industry Standard
    for API-scale systems is to use the astronomically rigorous Umm al-Qura calendar
    and apply regional offsets based on the country's local sighting committee practices.
    """
    # 1. Get regional offset based on historical sighting zones
    offset = get_regional_offset(country_code)

    # 2. Apply adjustment
    # Note: Shifting the Gregorian date before conversion accurately shifts the
    # lunar month window, effectively delaying or advancing the Hijri month start.
    adjusted_date = gregorian_date + timedelta(days=offset)

    # 3. Perform conversion using standardized Umm al-Qura library
    hijri = Gregorian(
        adjusted_date.year, adjusted_date.month, adjusted_date.day
    ).to_hijri()

    return HijriDateResponse(
        day=hijri.day, month=hijri.month, year=hijri.year, month_name=hijri.month_name()
    )
