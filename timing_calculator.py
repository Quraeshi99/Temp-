import datetime
import json
import structlog
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
from app.core.constants import PRAYER_CONFIG_MAP
from app.core.time_helpers import parse_time, format_time, add_minutes

logger = structlog.get_logger(__name__)

class CorrectionMode(Enum):
    STRICT = "STRICT"
    SAFE_START = "SAFE_START"
    NEAREST = "NEAREST"

def _get_minute_distance(t1: datetime.time, t2: datetime.time) -> int:
    """Calculates the shortest minute distance between two times, handling midnight wrap-around."""
    m1 = t1.hour * 60 + t1.minute
    m2 = t2.hour * 60 + t2.minute
    diff = abs(m1 - m2)
    return min(diff, 1440 - diff)

# --- LAYER 1: PURE MATHEMATICAL VALIDATOR ---
def validate_time_bounds(
    time_val: datetime.time, 
    start_val: datetime.time, 
    end_val: datetime.time, 
    buffer_mins: int
) -> Dict[str, Any]:
    """Rich validation response with distances and suggested corrections."""
    end_with_buffer = add_minutes(end_val, -buffer_mins)
    is_midnight = end_val < start_val
    
    is_valid = False
    reason = "ok"
    
    if not is_midnight:
        if time_val < start_val:
            reason, is_valid = "crossed_start_boundary", False
        elif time_val > end_with_buffer:
            reason, is_valid = "crossed_end_buffer", False
        else:
            is_valid = True
    else:
        # Midnight crossing (e.g., Isha 20:00 to Fajr 04:00)
        is_valid = (time_val >= start_val) or (time_val <= end_with_buffer)
        if not is_valid:
            reason = "out_of_midnight_bounds"

    dist_start = _get_minute_distance(time_val, start_val)
    dist_end = _get_minute_distance(time_val, end_with_buffer)
    suggested = start_val if dist_start <= dist_end else end_with_buffer

    return {
        "valid": is_valid,
        "reason": reason,
        "dist_start": dist_start,
        "dist_end": dist_end,
        "suggested": suggested
    }

# --- LAYER 2: DOMAIN RULE (NAMAZ SAFETY) ---
def apply_domain_correction(
    time_val: Optional[datetime.time],
    start_boundary_str: Optional[str],
    end_boundary_str: Optional[str],
    prayer_name: str,
    time_type: str,
    mode: CorrectionMode = CorrectionMode.SAFE_START,
    buffer_mins: int = 8
) -> Tuple[Optional[datetime.time], Optional[str]]:
    if not time_val:
        return None, None

    start_obj = parse_time(start_boundary_str)
    end_obj = parse_time(end_boundary_str)

    if not start_obj or not end_obj:
        return time_val, None

    val = validate_time_bounds(time_val, start_obj, end_obj, buffer_mins)
    
    if val["valid"]:
        return time_val, None

    if mode == CorrectionMode.STRICT:
        raise ValueError(f"Time violation for {prayer_name} {time_type}: {val['reason']}")
    
    # Decide final time based on Mode
    final_time = start_obj if mode == CorrectionMode.SAFE_START else val["suggested"]
    
    warning = f"Corrected {prayer_name} {time_type} due to {val['reason']}. Snapped to {'Start' if final_time == start_obj else 'End Buffer'}."
    
    logger.warning("time_correction_applied", 
        prayer=prayer_name, 
        type=time_type,
        reason=val["reason"], 
        original=format_time(time_val), 
        corrected=format_time(final_time)
    )

    return final_time, warning

def get_single_prayer_info(
    p_key: str,
    config: Dict[str, Any],
    user_settings: Any,
    api_times_today: Dict[str, Any],
    api_times_tomorrow: Dict[str, Any],
    last_api_times: Dict[str, Any],
    calculation_date: datetime.date,
) -> Tuple[Dict[str, str], bool, List[str]]:
    warnings = []
    needs_db_update_for_prayer = False
    prayer_display_name = p_key.capitalize()
    azan_time_obj, jamaat_time_obj = None, None

    api_start_time_str = api_times_today.get(config["api_key"])
    start_boundary_str = api_start_time_str
    end_boundary_key = config["end_boundary_key"]

    if end_boundary_key == "Fajr_Tomorrow":
        end_boundary_str = api_times_tomorrow.get("Fajr")
    else:
        end_boundary_str = api_times_today.get(end_boundary_key)

    is_fixed = getattr(user_settings, config["is_fixed_attr"], False)

    if is_fixed:
        azan_time_obj = parse_time(getattr(user_settings, config["fixed_azan_attr"]))
        jamaat_time_obj = parse_time(getattr(user_settings, config["fixed_jamaat_attr"]))

        azan_time_obj, azan_warning = apply_domain_correction(
            azan_time_obj, start_boundary_str, end_boundary_str, prayer_display_name, "Azan"
        )
        if azan_warning: warnings.append(azan_warning)

        jamaat_time_obj, jamaat_warning = apply_domain_correction(
            jamaat_time_obj, start_boundary_str, end_boundary_str, prayer_display_name, "Jamaat"
        )
        if jamaat_warning: warnings.append(jamaat_warning)
    else:
        if api_start_time_str:
            # Threshold/Sticky Logic
            api_time_to_use_str = api_start_time_str
            last_api_time_str = last_api_times.get(config["api_key"])

            # Per-Namaz Threshold Logic (Industry Best Practice)
            p_threshold_attr = f"{p_key}_threshold"
            threshold = getattr(user_settings, p_threshold_attr, 0)
            if threshold == 0:
                threshold = getattr(user_settings, "threshold_minutes", 0)

            if last_api_time_str and threshold > 0:
                last_time_obj = parse_time(last_api_time_str)
                new_time_obj = parse_time(api_start_time_str)
                if last_time_obj and new_time_obj:
                    diff = abs((datetime.datetime.combine(calculation_date, new_time_obj) - 
                               datetime.datetime.combine(calculation_date, last_time_obj)).total_seconds() / 60)
                    if diff < threshold:
                        api_time_to_use_str = last_api_time_str
                    else:
                        needs_db_update_for_prayer = True
                else: needs_db_update_for_prayer = True
            else: needs_db_update_for_prayer = True

            api_start_time_obj = parse_time(api_time_to_use_str)
            if api_start_time_obj:
                azan_offset = getattr(user_settings, config["azan_offset_attr"], 0)
                calculated_azan_obj = add_minutes(api_start_time_obj, azan_offset)
                azan_time_obj, azan_warning = apply_domain_correction(
                    calculated_azan_obj, start_boundary_str, end_boundary_str, prayer_display_name, "Azan"
                )
                if azan_warning: warnings.append(azan_warning)

                if azan_time_obj:
                    jamaat_offset = getattr(user_settings, config["jamaat_offset_attr"], 0)
                    calculated_jamaat_obj = add_minutes(azan_time_obj, jamaat_offset)
                    jamaat_time_obj, jamaat_warning = apply_domain_correction(
                        calculated_jamaat_obj, start_boundary_str, end_boundary_str, prayer_display_name, "Jamaat"
                    )
                    if jamaat_warning: warnings.append(jamaat_warning)

    return (
        {"azan": format_time(azan_time_obj), "jamaat": format_time(jamaat_time_obj)},
        needs_db_update_for_prayer,
        warnings,
    )

def calculate_other_times(api_times_today: Dict[str, Any], calculation_date: datetime.date) -> Dict[str, Any]:
    """Calculates supplementary times like Ishraq, Duha and Zohwa-e-Kubra."""
    sunrise_time_str = api_times_today.get("Sunrise")
    dhuhr_time_str = api_times_today.get("Dhuhr")
    fajr_time_str = api_times_today.get("Fajr")
    sunset_time_str = api_times_today.get("Sunset")

    # Helpers
    sunrise_obj = parse_time(sunrise_time_str)
    dhuhr_obj = parse_time(dhuhr_time_str)
    fajr_obj = parse_time(fajr_time_str)
    sunset_obj = parse_time(sunset_time_str)

    ishraq_time = add_minutes(sunrise_obj, 20) if sunrise_obj else None
    
    duha_time = None
    if sunrise_obj and dhuhr_obj:
        s_dt = datetime.datetime.combine(calculation_date, sunrise_obj)
        d_dt = datetime.datetime.combine(calculation_date, dhuhr_obj)
        if d_dt < s_dt: d_dt += datetime.timedelta(days=1)
        duha_time = (s_dt + (d_dt - s_dt) / 2).time()

    zohwa_start = None
    if fajr_obj and sunset_obj:
        f_dt = datetime.datetime.combine(calculation_date, fajr_obj)
        su_dt = datetime.datetime.combine(calculation_date, sunset_obj)
        if su_dt < f_dt: su_dt += datetime.timedelta(days=1)
        zohwa_start = (f_dt + (su_dt - f_dt) / 2).time()

    zohwa_end = None
    if sunrise_obj and sunset_obj:
        s_dt = datetime.datetime.combine(calculation_date, sunrise_obj)
        su_dt = datetime.datetime.combine(calculation_date, sunset_obj)
        if su_dt < s_dt: su_dt += datetime.timedelta(days=1)
        zohwa_end = (s_dt + (su_dt - s_dt) / 2).time()

    zawal_start = add_minutes(dhuhr_obj, -15) if dhuhr_obj else None

    return {
        "ishraq": {"time": format_time(ishraq_time)},
        "duha": {"time": format_time(duha_time)},
        "zohwa_kubra": {"start": format_time(zohwa_start), "end": format_time(zohwa_end)},
        "zawal": {"start": format_time(zawal_start), "end": dhuhr_time_str},
    }

def _calculate_jummah_times(user_settings: Any, dhuhr_raw_time_str: Optional[str]) -> Dict[str, str]:
    """Calculates Jummah times with fallback to Dhuhr and automatic Khutbah."""
    is_fixed = getattr(user_settings, "jummah_is_fixed", True)
    j_azan, j_jamaat, j_khutbah = None, None, None
    d_obj = parse_time(dhuhr_raw_time_str)

    if is_fixed:
        j_azan = parse_time(getattr(user_settings, "jummah_azan_time", None))
        j_jamaat = parse_time(getattr(user_settings, "jummah_jamaat_time", None))
        # Fallback if fixed times are empty
        if not j_azan and d_obj: j_azan = d_obj
        if not j_jamaat and j_azan: j_jamaat = add_minutes(j_azan, 15) # Default 15m after azan
    else:
        j_azan = add_minutes(d_obj, getattr(user_settings, "jummah_azan_offset", 0)) if d_obj else None
        j_jamaat = add_minutes(j_azan, getattr(user_settings, "jummah_jamaat_offset", 0)) if j_azan else None

    # Khutbah is calculated based on masjid/user offset (default 5 mins before jamaat)
    if j_jamaat:
        offset = getattr(user_settings, "jummah_khutbah_offset", 5)
        # We subtract the offset (e.g., 5 mins before)
        j_khutbah = add_minutes(j_jamaat, -abs(offset))

    return {
        "azan": format_time(j_azan), 
        "jamaat": format_time(j_jamaat), 
        "khutbah": format_time(j_khutbah)
    }

def calculate_display_times(
    user_settings: Any,
    api_times_today: Dict[str, Any],
    api_times_tomorrow: Dict[str, Any],
    calculation_date: datetime.date,
) -> Tuple[Dict[str, Any], bool, List[str]]:
    calculated_times = {}
    needs_db_update = False
    warnings = []

    last_api_times = {}
    if getattr(user_settings, "last_api_times_for_threshold", None):
        try: last_api_times = json.loads(user_settings.last_api_times_for_threshold)
        except: needs_db_update = True

    for p_key, config in PRAYER_CONFIG_MAP.items():
        p_times, needs_update, p_warnings = get_single_prayer_info(
            p_key, config, user_settings, api_times_today, api_times_tomorrow, last_api_times, calculation_date
        )
        calculated_times[p_key] = p_times
        if p_warnings: warnings.extend(p_warnings)
        if needs_update: needs_db_update = True

    calculated_times["iftari"] = {"time": calculated_times["maghrib"]["azan"]}
    calculated_times["sehri_end"] = {"time": format_time(parse_time(api_times_today.get("Imsak")))}
    calculated_times["midnight"] = {"time": format_time(parse_time(api_times_today.get("Midnight")))}
    calculated_times["tahajjud"] = {"time": format_time(parse_time(api_times_today.get("Lastthird")))}
    calculated_times["jummah"] = _calculate_jummah_times(user_settings, api_times_today.get("Dhuhr"))
    calculated_times.update(calculate_other_times(api_times_today, calculation_date))
    
    return calculated_times, needs_db_update, warnings

def get_method_id_from_key(method_key: str) -> int:
    mapping = {"Jafari": 0, "Karachi": 1, "ISNA": 2, "MWL": 3, "Makkah": 4, "Egyptian": 5, "Barelvi": 20, "Dubai": 16, "Community": 99}
    return mapping.get(method_key, 2)

def get_current_prayer_period(
    api_times_today: Dict[str, Any],
    api_times_tomorrow: Dict[str, Any],
    now_datetime_obj: datetime.datetime,
) -> Dict[str, str]:
    if not api_times_today:
        return {"name": "N/A", "start": "N/A", "end": "N/A"}
    now_time = now_datetime_obj.time()
    periods_config = [
        ("Fajr", "Fajr", "Sunrise"),
        ("Post-Sunrise", "Sunrise", "Dhuhr"),
        ("Dhuhr", "Dhuhr", "Asr"),
        ("Asr", "Asr", "Maghrib"),
        ("Maghrib", "Maghrib", "Isha"),
        ("Isha", "Isha", "Fajr_Tomorrow"),
    ]
    for p_name, start_key, end_key in periods_config:
        start_time_str = api_times_today.get(start_key)
        end_time_str = (
            api_times_tomorrow.get("Fajr")
            if end_key == "Fajr_Tomorrow" and api_times_tomorrow
            else api_times_today.get(end_key)
        )
        start_obj, end_obj = parse_time(start_time_str), parse_time(end_time_str)
        if start_obj and end_obj:
            if start_obj > end_obj:  # Midnight crossing (Isha -> Fajr)
                if (now_time >= start_obj) or (now_time < end_obj):
                    return {
                        "name": p_name.upper(),
                        "start": start_time_str,
                        "end": end_time_str,
                    }
            elif start_obj <= now_time < end_obj:
                return {
                    "name": p_name.upper(),
                    "start": start_time_str,
                    "end": end_time_str,
                }
    return {"name": "N/A", "start": "N/A", "end": "N/A"}

def get_prayer_key_for_tomorrow(
    current_prayer_name: str, today_date: datetime.date
) -> str:
    """Special logic for tomorrow's display (Thursday -> Jummah, Friday -> Dhuhr)."""
    key = current_prayer_name.capitalize()
    main_keys = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    if key not in main_keys:
        key = "Fajr"

    weekday = today_date.weekday()  # Mon=0, Thu=3, Fri=4
    if weekday == 3 and current_prayer_name.upper() == "DHUHR":
        key = "Jummah"
    elif weekday == 4 and current_prayer_name.upper() == "DHUHR":
        key = "Dhuhr"
    return key
