import re

# Keywords list that suggests actual disaster signals
DISASTER_KEYWORDS = [
    "earthquake", "quake", "tremor", "seismic", "richter", "epicenter",
    "flood", "inundation", "overflow", "monsoon", "rain", "deluge", "torrential",
    "landslide", "mudslide", "avalanche", "disaster", "emergency", "ndma",
    "casualty", "casualties", "evacuate", "evacuation", "rescue", "relief", "cyclone",
    "storm", "tsunami", "drought", "alert", "outbreak", "epidemic"
]

def clean_text(text):
    """
    Cleans raw text: removes HTML tags, URLs, and extra whitespaces.
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r"<[^>]*>", " ", text)
    
    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    
    # Replace multiple spaces/newlines/tabs with a single space
    text = re.sub(r"\s+", " ", text)
    
    # Strip spaces before punctuation marks
    text = re.sub(r"\s+([!,.:;?])", r"\1", text)
    
    return text.strip()

def is_disaster_related(text):
    """
    Checks if the text contains disaster-related keywords to filter out non-disaster chatter.
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in DISASTER_KEYWORDS)

def clean_and_filter(raw_reports):
    """
    Cleans, deduplicates, and filters raw reports to produce clean_reports.
    """
    cleaned_reports = []
    seen_ids = set()
    seen_texts = set()
    
    for report in raw_reports:
        # 1. Deduplicate by unique ID
        report_id = report.get("id")
        if not report_id or report_id in seen_ids:
            continue
            
        # 2. Clean text
        text = report.get("text", "")
        cleaned_txt = clean_text(text)
        
        # 3. Filter out if empty or not disaster-related (skip keyword check for structured sources)
        is_structured = report.get("source") in ["usgs", "gdacs", "reliefweb"]
        if not cleaned_txt or (not is_structured and not is_disaster_related(cleaned_txt)):
            continue
            
        # 4. Deduplicate by text signature (to catch similar reports from different feeds)
        text_sig = re.sub(r"\W+", "", cleaned_txt.lower())
        if text_sig in seen_texts:
            continue
            
        seen_ids.add(report_id)
        seen_texts.add(text_sig)
        
        # Construct clean report
        clean_rep = {
            "id": report_id,
            "source": report.get("source"),
            "text": cleaned_txt,
            "location_text": clean_text(report.get("location_text", "Pakistan")),
            "timestamp": report.get("timestamp")
        }
        cleaned_reports.append(clean_rep)
        
    return cleaned_reports
