# Smart Disaster Ingestion Pipeline (Pakistan)

A high-performance data ingestion pipeline that fetches real-time and historical disaster events (earthquakes, floods, landslides, extreme weather) in Pakistan from multiple sources. It cleans, deduplicates, and labels the unstructured data to construct a ready-to-use dataset for ML training.

## 📊 Features & Current Status

- **USGS Integration:** Pulls historical earthquake data (from 2020 onwards) within Pakistan's geographic bounding box.
- **GDACS Integration:** Fetches global disaster alerts filtered specifically for Pakistan (`PAK`).
- **Reddit Ingestion:** Includes a fallback simulator and PRAW implementation to fetch live disaster discussions from `r/pakistan`.
- **Deduplication & Cleaning:** Cleans HTML tags, URLs, and duplicates raw reports using text signatures.
- **Heuristic Labeling Engine:** Categorizes disasters into `earthquake`, `flood`, `landslide`, or `other`, resolves locations to Pakistan's districts/provinces, and rates hazard priority (`low`, `medium`, `high`, `critical`).

---

## 📂 Project Structure

```
├── .gitignore               # Excludes python cache, config, and intermediate logs/files
├── README.md                # Project documentation
├── config.py.example        # Configuration template (rename to config.py)
├── fetchers.py              # Logic to query APIs (USGS, GDACS, GDELT, ReliefWeb, Reddit)
├── normalizer.py            # Formats API responses into a unified schema
├── cleaner.py               # Cleans text & removes duplicates
├── labeler.py               # Rule-based ML labeler & location resolver
├── pipeline.py              # Main orchestrator (runs once or in a continuous loop)
└── training_dataset.json    # The generated dataset for the ML team (1,395 records)
```

---

## 🚀 Getting Started

### 1. Clone & Install Dependencies
Ensure you have Python 3.8+ installed. Install the requirements:
```bash
pip install requests praw
```

### 2. Configure Credentials
1. Rename `config.py.example` to `config.py`:
   ```bash
   cp config.py.example config.py
   ```
2. Open `config.py` and replace placeholders with your Reddit API keys (required for live Reddit ingestion).

### 3. Run the Pipeline
Run the pipeline once to fetch new updates:
```bash
python pipeline.py --once
```

Or run the pipeline as a background service checking for updates every 60 seconds (default):
```bash
python pipeline.py --interval 60
```

---

## 📦 ML Dataset Format (`training_dataset.json`)

The final training dataset is saved as a JSON array. Each object has the following schema:

```json
{
  "text": "Flooding reported in Swat Valley after heavy monsoon rains, houses damaged",
  "location": "Khyber Pakhtunkhwa",
  "label": "flood",
  "priority": "high"
}
```

- **`text`**: Cleaned raw text.
- **`location`**: Resolved Pakistan province/district/city (default: "Pakistan").
- **`label`**: Categorized disaster type (`earthquake`, `flood`, `landslide`, `other`).
- **`priority`**: Severity index (`low`, `medium`, `high`, `critical`).
