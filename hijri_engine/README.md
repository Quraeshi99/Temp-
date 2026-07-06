# 🌙 Hijri Engine

## Overview
A regional-aware Hijri date conversion system.

## Smart Features
1. **Regional Offsets:** Automatically detects country zones (e.g., India/Pakistan) to adjust for local moon-sighting (-1 day from Saudi astronomical date).
2. **Zonal Mapping:** Categorizes 200+ countries into 3 main sighting zones.
3. **Accuracy:** Uses Umm al-Qura base algorithms with regional override layers.

## Usage
Provide the ISO Country Code (e.g., `country_code=IN`) to get the locally observed Hijri date.

## Event & Holiday Architecture (v2)
This engine automatically fetches Islamic and National Public Holidays for any given country.
We use a **Smart Deduplication Engine** that prevents duplicate holidays (e.g., when a National Holiday is also an Islamic Holiday).

### Data Schema (For Frontend Developers)
The backend now returns a structured, FAANG-level JSON schema for events. **Frontend should NOT expect pre-formatted strings.**

```json
{
  "event_id": "eid_al_fitr",
  "local_name": "Hari Raya Idul Fitri", // null if not available
  "display_name": "Hari Raya Idul Fitri", // Always Romanized (ASCII) for global readability
  "english_name": "Eid al-Fitr",
  "arabic_name": "عيد الفطر", // null for National Holidays
  "type": "EID", // EID, PUBLIC_HOLIDAY, OBSERVANCE, etc.
  "hijri_date": "1 Shawwal 1447",
  "sources": ["islamic_engine", "holidays"] // Useful for debugging overlap
}
```

### Key Behaviors
- **Confidence Scoring Engine:** A strict 100-point scoring system merges overlapping Islamic and National holidays (requires exact Event ID, exact Date, or Global Alias keyword match).
- **No Overlapping Clashes:** If a pure National Holiday (e.g. Republic Day) coincides with an Islamic Event, they are returned as **two separate objects** in the array.
- **Transliteration:** Cyrillic (e.g., `Орозо`), Bengali (`ঈদুল`), etc., are automatically converted to English characters in `display_name` via `anyascii` for universal readability.
- **Null Fallbacks:** We strictly use `null` instead of empty strings `""` or `"-"` for missing data to allow robust frontend conditionals.
- **Dumb Frontend Friendly:** The frontend has total control to style the local name prominently and the English/Arabic name secondarily. Do not concatenate strings on the backend.
