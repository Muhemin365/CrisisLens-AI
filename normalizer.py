import datetime
import re

def parse_timestamp(source, raw_ts):
    """
    Parses various timestamp formats into a unified ISO-8601 UTC string: YYYY-MM-DDTHH:MM:SSZ
    """
    if not raw_ts:
        return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        if source == "usgs":
            # USGS provides epoch milliseconds
            dt = datetime.datetime.utcfromtimestamp(float(raw_ts) / 1000.0)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            
        elif source == "reddit":
            # Reddit provides epoch seconds
            dt = datetime.datetime.utcfromtimestamp(float(raw_ts))
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            
        elif source == "gdelt":
            # GDELT uses YYYYMMDDHHMMSS format, e.g. "20260612100000"
            ts_str = str(raw_ts)
            # Remove any non-digits
            ts_str = re.sub(r"\D", "", ts_str)
            if len(ts_str) >= 8:
                year = int(ts_str[0:4])
                month = int(ts_str[4:6])
                day = int(ts_str[6:8])
                hour = int(ts_str[8:10]) if len(ts_str) >= 10 else 0
                minute = int(ts_str[10:12]) if len(ts_str) >= 12 else 0
                second = int(ts_str[12:14]) if len(ts_str) >= 14 else 0
                dt = datetime.datetime(year, month, day, hour, minute, second)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                
        elif source == "reliefweb":
            # ReliefWeb returns ISO-8601, e.g., "2026-06-12T10:00:00+00:00"
            # Normalize to UTC Z format
            ts_str = str(raw_ts)
            # Simple conversion if it ends with +00:00 or similar
            if "+" in ts_str:
                ts_str = ts_str.split("+")[0]
            if not ts_str.endswith("Z"):
                ts_str += "Z"
            return ts_str
            
    except Exception as e:
        print(f"[Normalizer Warning] Failed to parse timestamp {raw_ts} for source {source}: {e}")
        
    # Fallback to current time if parsing fails
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def normalize_report(report):
    """
    Normalizes a single report to the unified raw_reports schema.
    """
    source = report.get("source")
    raw_ts = report.get("timestamp")
    
    normalized_ts = parse_timestamp(source, raw_ts)
    
    return {
        "id": report.get("id"),
        "source": source,
        "text": report.get("text", "").strip(),
        "location_text": report.get("location_text", "Pakistan").strip(),
        "timestamp": normalized_ts,
        "raw_data": report.get("raw_data", {})
    }

def normalize_all(reports):
    """
    Normalizes a list of raw reports.
    """
    normalized = []
    for r in reports:
        if r.get("id") and r.get("source"):
            normalized.append(normalize_report(r))
    return normalized
