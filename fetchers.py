import os
import time
import requests
import random

# Import credentials from config
try:
    from config import (
        REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
        RELIEFWEB_APP_NAME
    )
except ImportError:
    REDDIT_CLIENT_ID     = ""
    REDDIT_CLIENT_SECRET = ""
    REDDIT_USER_AGENT    = "disaster_pipeline:v1.0"
    RELIEFWEB_APP_NAME   = "smart-disaster-pipeline"

# ─────────────────────────────────────────────
# Pakistan Bounding Box for geographic filtering
# ─────────────────────────────────────────────
PAK_BBOX = {
    "minlatitude":  23.5,
    "maxlatitude":  37.0,
    "minlongitude": 60.8,
    "maxlongitude": 77.0
}

# ─────────────────────────────────────────────
# 1. USGS — Free, No Key Required
# ─────────────────────────────────────────────
def fetch_usgs():
    """
    Fetches real-time earthquake data from USGS within Pakistan's bounding box.
    No API key required.
    """
    print("[USGS] Fetching earthquake data for Pakistan...")
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "minmagnitude": "3.0",
        "starttime": "2020-01-01",  # Fetch history from 2020 onwards
        **PAK_BBOX
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        reports = []
        for event in data.get("features", []):
            props = event.get("properties", {})
            reports.append({
                "id": f"usgs_{event.get('id') or props.get('time')}",
                "source": "usgs",
                "text": props.get("title", "No Title"),
                "location_text": props.get("place", "Pakistan"),
                "timestamp": props.get("time"),
                "raw_data": props
            })
        print(f"[USGS] [OK] {len(reports)} earthquake reports fetched.")
        return reports
    except Exception as e:
        print(f"[USGS] [ERROR] Failed: {e}")
        return []

# ─────────────────────────────────────────────
# 2. GDELT — Free, No Key Required
# ─────────────────────────────────────────────
def fetch_gdelt():
    """
    Queries GDELT for Pakistan disaster news articles.
    No API key required.
    """
    print("[GDELT] Fetching Pakistan disaster news...")
    query = "Pakistan (flood OR earthquake OR landslide OR disaster OR monsoon)"
    # Increased maxrecords from 20 to 250
    url = (
        f"https://api.gdeltproject.org/api/v2/doc/doc"
        f"?query={requests.utils.quote(query)}&format=json&maxrecords=250"
    )
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()
        reports = []
        for item in data.get("articles", []):
            reports.append({
                "id": f"gdelt_{hash(item.get('url', ''))}",
                "source": "gdelt",
                "text": item.get("title", "No Title"),
                "location_text": "Pakistan",
                "timestamp": item.get("seendate"),
                "raw_data": item
            })
        print(f"[GDELT] [OK] {len(reports)} news reports fetched.")
        return reports
    except Exception as e:
        print(f"[GDELT] [ERROR] Failed: {e}")
        return []

# ─────────────────────────────────────────────
# 3. GDACS — Free, No Key Required
# ─────────────────────────────────────────────
def fetch_gdacs():
    """
    Queries GDACS (Global Disaster Alert and Coordination System) for Pakistan events.
    No API key required.
    """
    print("[GDACS] Fetching disaster alerts for Pakistan...")
    url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
    params = {
        "eventlist": "FL,EQ,TC",  # Flood, Earthquake, Tropical Cyclone
        "fromdate": "2020-01-01",  # Fetch history from 2020 onwards
        "todate": "",
        "alertlevel": "Red,Orange,Green",
        "country": "PAK"
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        reports = []
        for item in data.get("features", []):
            props = item.get("properties", {})
            reports.append({
                "id": f"gdacs_{props.get('eventid', '')}_{props.get('episodeid', '')}",
                "source": "gdacs",
                "text": props.get("name", "GDACS Alert"),
                "location_text": props.get("country", "Pakistan"),
                "timestamp": props.get("fromdate"),
                "raw_data": props
            })
        print(f"[GDACS] [OK] {len(reports)} disaster alerts fetched.")
        return reports
    except Exception as e:
        print(f"[GDACS] [ERROR] Failed: {e}")
        return []

# ─────────────────────────────────────────────
# 4. ReliefWeb — Free, No Key Required
# ─────────────────────────────────────────────
def fetch_reliefweb():
    """
    Fetches Pakistan disaster situation reports from ReliefWeb.
    No API key required.
    """
    print("[ReliefWeb] Fetching Pakistan situation reports...")
    url = f"https://api.reliefweb.int/v2/reports?appname={RELIEFWEB_APP_NAME}"
    payload = {
        "filter": {
            "operator": "AND",
            "conditions": [
                {"field": "primary_country.iso3", "value": "pak"},
                {
                    "field": "theme.name",
                    "value": ["Earthquake and Tsunami", "Floods", "Landslides and Mudslides"],
                    "operator": "OR"
                }
            ]
        },
        "fields": {"include": ["title", "date", "primary_country", "theme"]},
        "limit": 1000,
        "sort": ["date.created:desc"]
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        res.raise_for_status()
        data = res.json()
        reports = []
        for item in data.get("data", []):
            fields = item.get("fields", {})
            reports.append({
                "id": f"reliefweb_{item.get('id')}",
                "source": "reliefweb",
                "text": fields.get("title", "No Title"),
                "location_text": "Pakistan",
                "timestamp": fields.get("date", {}).get("created"),
                "raw_data": fields
            })
        print(f"[ReliefWeb] [OK] {len(reports)} situation reports fetched.")
        return reports
    except Exception as e:
        print(f"[ReliefWeb] [ERROR] Failed: {e}")
        return []

# ─────────────────────────────────────────────
# 5. Reddit — Free Key (get at reddit.com/prefs/apps)
# ─────────────────────────────────────────────
def get_simulated_reddit_posts():
    """
    Generates realistic Pakistan-focused mock Reddit posts for fallback/enrichment.
    Used when Reddit API is unavailable or credentials are not set.
    """
    topics = [
        {"title": "Flooding reported in Swat Valley after heavy monsoon rains, houses damaged", "loc": "Swat Valley, KP"},
        {"title": "Moderate earthquake tremor felt in Islamabad and northern areas", "loc": "Islamabad"},
        {"title": "Landslides block Karakoram Highway near Gilgit, traffic suspended", "loc": "Gilgit-Baltistan"},
        {"title": "NDMA issues alert for high flows in Indus River; Southern Punjab villages advised to relocate", "loc": "Southern Punjab"},
        {"title": "Heavy urban flooding in Karachi streets after continuous 8-hour rain", "loc": "Karachi, Sindh"},
        {"title": "Tremors felt in Quetta, magnitude estimated 4.5 by meteorological dept", "loc": "Quetta, Balochistan"},
        {"title": "Relief activities ongoing in flood-affected districts of Balochistan", "loc": "Balochistan"},
        {"title": "Glacial lake outburst flood (GLOF) reported in Hunza, local bridge swept away", "loc": "Hunza, Gilgit-Baltistan"},
        {"title": "26 dead after flash floods in Dera Ismail Khan, rescue teams deployed", "loc": "Dera Ismail Khan, KP"},
        {"title": "Sukkur barrage water level rising dangerously, authorities on high alert", "loc": "Sukkur, Sindh"},
    ]
    selected = random.sample(topics, min(4, len(topics)))
    current_time = int(time.time())
    return [
        {
            "id": f"reddit_sim_{current_time}_{i}",
            "source": "reddit",
            "text": t["title"],
            "location_text": t["loc"],
            "timestamp": current_time,
            "raw_data": {"simulated": True, "score": random.randint(10, 500)}
        }
        for i, t in enumerate(selected)
    ]

def fetch_reddit():
    """
    Fetches Pakistan disaster posts using PRAW (real credentials) or falls back to
    the public JSON API. If both fail, returns simulated Pakistan disaster posts.
    """
    print("[Reddit] Fetching r/pakistan disaster posts...")

    # ── Attempt 1: PRAW with real credentials ──
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_ID != "YOUR_CLIENT_ID_HERE":
        try:
            import praw
            reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )
            subreddits = ["pakistan", "PakistanWeather", "WorldNews"]
            keywords = ["flood", "earthquake", "quake", "rain", "landslide", "disaster", "NDMA", "relief"]
            reports = []
            for sub in subreddits:
                for post in reddit.subreddit(sub).search(
                    " OR ".join(keywords), sort="new", limit=10
                ):
                    reports.append({
                        "id": f"reddit_{post.id}",
                        "source": "reddit",
                        "text": post.title,
                        "location_text": "Pakistan",
                        "timestamp": post.created_utc,
                        "raw_data": {"score": post.score, "url": post.url}
                    })
            print(f"[Reddit] [OK] {len(reports)} posts fetched via PRAW.")
            return reports
        except Exception as e:
            print(f"[Reddit] PRAW failed: {e}. Trying public JSON API...")

    # -- Attempt 2: Public JSON API (no auth) --
    try:
        headers = {"User-Agent": "disaster-tracker-agent:v1.0.0"}
        url = (
            "https://www.reddit.com/r/pakistan/search.json"
            "?q=flood+OR+earthquake+OR+rain+OR+landslide+OR+disaster"
            "&restrict_sr=1&sort=new&limit=10"
        )
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 429:
            raise Exception("Rate limited (429)")
        res.raise_for_status()
        data = res.json()
        reports = []
        for post in data.get("data", {}).get("children", []):
            d = post.get("data", {})
            reports.append({
                "id": f"reddit_{d.get('id')}",
                "source": "reddit",
                "text": d.get("title", ""),
                "location_text": "Pakistan",
                "timestamp": d.get("created_utc"),
                "raw_data": {"score": d.get("score"), "url": d.get("url")}
            })
        print(f"[Reddit] [OK] {len(reports)} posts fetched via public API.")
        return reports
    except Exception as e:
        print(f"[Reddit] [ERROR] Public API failed: {e}. Using simulated fallback.")
        posts = get_simulated_reddit_posts()
        print(f"[Reddit] [OK] {len(posts)} simulated posts generated.")
        return posts
