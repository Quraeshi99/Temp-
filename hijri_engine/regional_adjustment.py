class HijriZone:
    """
    Groups countries based on their standard moon-sighting practices.
    """

    # Zone 1: Often 1 day BEHIND Saudi (Local Sighting focus)
    ZONE_LOCAL_SIGHTING = ["IN", "PK", "BD", "OM", "MA", "ZA", "GB"]
    # Zone 2: Following Saudi Arabia (Umm al-Qura)
    ZONE_SAUDI_CENTRIC = ["SA", "AE", "QA", "KW", "BH", "JO", "EG"]
    # Zone 3: Southeast Asia (Often unique sighting)
    ZONE_SEA = ["ID", "MY", "BN", "SG"]


def get_regional_offset(country_code: str) -> int:
    """
    Returns the standard Hijri offset for a country relative to the
    central astronomical calculation.

    RATIONALE:
    AlAdhan API gives a flat date. Our engine identifies the country
    and applies an offset to match local reality (e.g., India is
    typically 1 day behind Saudi).
    """
    cc = country_code.upper()

    if cc in HijriZone.ZONE_LOCAL_SIGHTING:
        # Standard adjustment for South Asia/Morocco/UK locals
        return -1

    if cc in HijriZone.ZONE_SEA:
        # Southeast Asia sighting logic (varies, but often -1 from Astro)
        return -1

    # Default: 0 offset (Astro/Saudi match)
    return 0
