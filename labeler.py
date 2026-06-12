import re

# Lexicon of Pakistan locations (provinces, territories, and major cities/regions)
PAK_LOCATIONS = {
    # Provinces & Regions
    "punjab": "Punjab",
    "sindh": "Sindh",
    "balochistan": "Balochistan",
    "khyber pakhtunkhwa": "Khyber Pakhtunkhwa",
    "kp": "Khyber Pakhtunkhwa",
    "kpk": "Khyber Pakhtunkhwa",
    "gilgit-baltistan": "Gilgit-Baltistan",
    "gb": "Gilgit-Baltistan",
    "azad kashmir": "Azad Kashmir",
    "ajk": "Azad Kashmir",
    "jammu & kashmir": "Azad Kashmir",
    
    # Major Cities/Districts
    "karachi": "Karachi, Sindh",
    "lahore": "Lahore, Punjab",
    "islamabad": "Islamabad Capital Territory",
    "rawalpindi": "Rawalpindi, Punjab",
    "peshawar": "Peshawar, Khyber Pakhtunkhwa",
    "quetta": "Quetta, Balochistan",
    "multan": "Multan, Punjab",
    "faisalabad": "Faisalabad, Punjab",
    "sialkot": "Sialkot, Punjab",
    "swat": "Swat, Khyber Pakhtunkhwa",
    "hunza": "Hunza, Gilgit-Baltistan",
    "gwadar": "Gwadar, Balochistan",
    "hyderabad": "Hyderabad, Sindh",
    "sukkur": "Sukkur, Sindh",
    "larkana": "Larkana, Sindh",
    "gilgit": "Gilgit, Gilgit-Baltistan",
    "skardu": "Skardu, Gilgit-Baltistan",
    "muzaffarabad": "Muzaffarabad, Azad Kashmir",
    "chitral": "Chitral, Khyber Pakhtunkhwa",
    "abbottabad": "Abbottabad, Khyber Pakhtunkhwa",
    "dera ismail khan": "Dera Ismail Khan, Khyber Pakhtunkhwa",
    "di khan": "Dera Ismail Khan, Khyber Pakhtunkhwa",
    "dera ghazi khan": "Dera Ghazi Khan, Punjab",
    "dg khan": "Dera Ghazi Khan, Punjab"
}

def resolve_location(text, location_text=""):
    """
    Resolves the specific Pakistan location from the report's text and location_text.
    """
    combined = f"{text} {location_text}".lower()
    
    # Try to find specific districts/cities first
    for key, value in PAK_LOCATIONS.items():
        # Match word boundaries to prevent substring collisions (e.g. "swat" inside "sweater")
        if re.search(r'\b' + re.escape(key) + r'\b', combined):
            return value
            
    return "Pakistan"

def classify_disaster(text):
    """
    Classifies the disaster type as earthquake, flood, landslide, or other.
    """
    text_lower = text.lower()
    
    if any(kw in text_lower for kw in ["earthquake", "quake", "tremor", "seismic", "epicenter"]):
        return "earthquake"
    elif any(kw in text_lower for kw in ["flood", "inundation", "overflow", "monsoon", "rain", "deluge", "torrential"]):
        return "flood"
    elif any(kw in text_lower for kw in ["landslide", "mudslide", "rockslide"]):
        return "landslide"
    else:
        return "other"

def parse_magnitude(text):
    """
    Extracts magnitude from text (e.g. "magnitude 5.2" or "M 5.2" or "5.2 magnitude")
    """
    match = re.search(r'(?:magnitude|mag|m)\s*(\d+\.\d+)', text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    match_reverse = re.search(r'(\d+\.\d+)\s*(?:magnitude|mag)', text, re.IGNORECASE)
    if match_reverse:
        return float(match_reverse.group(1))
    return None

def score_priority(text, label):
    """
    Heuristic-based priority scoring. Returns: low, medium, high, critical.
    """
    text_lower = text.lower()
    
    # 1. Critical Indicators
    # Mentions of death, casualties, or extreme devastation
    death_pattern = r"(\d+|many|several|dozens)\s+(dead|died|fatalities|casualties|killed|deaths)"
    if re.search(death_pattern, text_lower) or any(kw in text_lower for kw in ["state of emergency", "catastrophe", "devastating"]):
        return "critical"
        
    # Earthquake specific critical checks
    if label == "earthquake":
        mag = parse_magnitude(text)
        if mag and mag >= 6.0:
            return "critical"
        elif mag and mag >= 5.0:
            return "high"
            
    # Flood specific critical checks
    if label == "flood":
        if any(kw in text_lower for kw in ["sweep", "swept", "submerge", "dam burst", "wash away"]):
            return "critical"
            
    # 2. High Indicators
    high_keywords = ["damage", "injured", "blocked", "suspended", "evacuated", "homeless", "collapse", "displaced"]
    if any(kw in text_lower for kw in high_keywords):
        return "high"
        
    # 3. Medium Indicators
    medium_keywords = ["warning", "alert", "heavy rain", "inundated", "monsoon alert", "tremors felt"]
    if any(kw in text_lower for kw in medium_keywords):
        return "medium"
        
    if label == "earthquake":
        mag = parse_magnitude(text)
        if mag and mag >= 4.0:
            return "medium"
            
    # Default priority
    return "low"

def generate_labeled_report(clean_report):
    """
    Converts a clean report to the ML training format.
    """
    text = clean_report.get("text", "")
    loc_text = clean_report.get("location_text", "")
    
    resolved_loc = resolve_location(text, loc_text)
    disaster_label = classify_disaster(text)
    priority = score_priority(text, disaster_label)
    
    return {
        "text": text,
        "location": resolved_loc,
        "label": disaster_label,
        "priority": priority
    }

def label_all(clean_reports):
    """
    Labels a list of clean reports.
    """
    return [generate_labeled_report(r) for r in clean_reports]
