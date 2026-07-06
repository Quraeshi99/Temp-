"""
Shared constants for the Hijri Engine.
Single Source of Truth for Hijri month names and related constants.
Used by: hijri_oracle_service.py, raw_prayer_times_service.py, calendar_service.py
"""

# Hijri Month Names (Arabic transliteration)
HIJRI_MONTHS: dict[int, str] = {
    1: "Muharram",
    2: "Safar",
    3: "Rabi al-Awwal",
    4: "Rabi al-Thani",
    5: "Jumada al-Ula",
    6: "Jumada al-Thani",
    7: "Rajab",
    8: "Sha'ban",
    9: "Ramadan",
    10: "Shawwal",
    11: "Dhul Qi'dah",
    12: "Dhul Hijjah",
}

# Reverse lookup: name → number
HIJRI_MONTH_NUMBERS: dict[str, int] = {v: k for k, v in HIJRI_MONTHS.items()}

# Islamic month lengths: either 29 or 30 days (minimum 29, NEVER 28)
HIJRI_MIN_MONTH_DAYS = 29
HIJRI_MAX_MONTH_DAYS = 30

# Community Verification — Voting Configuration
# City tier weights for weighted voting system
CITY_TIER_WEIGHTS: dict[str, float] = {
    "METRO": 3.0,      # Population >= 1,000,000
    "DEFAULT": 1.0,     # Everything else (safe default, needs more votes)
}

# Points threshold to trigger a country-level Hijri date update
CONSENSUS_THRESHOLD: float = 9.0

# Hijri day from which moon-sighting votes are accepted
# Islamic months are 29 or 30 days, NEVER 28. So day 27 is safe.
VOTE_WINDOW_START_DAY: int = 27

# Population threshold for METRO classification
METRO_POPULATION_THRESHOLD: int = 1_000_000
