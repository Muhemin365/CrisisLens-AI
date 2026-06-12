import json
import time
import os
import argparse
from fetchers import fetch_usgs, fetch_gdelt, fetch_gdacs, fetch_reddit, fetch_reliefweb
from normalizer import normalize_all
from cleaner import clean_and_filter
from labeler import label_all

RAW_FILE = "raw_reports.json"
CLEAN_FILE = "clean_reports.json"
TRAINING_FILE = "training_dataset.json"

def load_existing_json(filepath):
    """
    Loads existing data from a JSON file, returning an empty list if not found or invalid.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Pipeline Warning] Failed to read {filepath}: {e}")
    return []

def save_json(data, filepath):
    """
    Saves data to a JSON file with proper indentation.
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[Pipeline] Successfully saved {len(data)} items to {filepath}")
    except Exception as e:
        print(f"[Pipeline Error] Failed to write to {filepath}: {e}")

def run_pipeline_cycle():
    """
    Executes a single cycle of the ingestion, cleaning, and labeling pipeline.
    """
    print("\n" + "="*50)
    print("Starting Pakistan Disaster Pipeline Execution Cycle")
    print("="*50)
    
    # 1. Fetch data from all sources
    raw_fetched = []
    raw_fetched += fetch_usgs()
    raw_fetched += fetch_gdelt()
    raw_fetched += fetch_gdacs()
    raw_fetched += fetch_reddit()
    raw_fetched += fetch_reliefweb()
    
    # 2. Normalize raw reports
    normalized_fetched = normalize_all(raw_fetched)
    
    # 3. Load existing raw reports and merge (preventing duplicates)
    existing_raw = load_existing_json(RAW_FILE)
    
    # Build maps of existing items by ID to avoid duplicates
    existing_raw_map = {r["id"]: r for r in existing_raw}
    
    new_raw_count = 0
    for report in normalized_fetched:
        report_id = report["id"]
        # If new or has updated data, update/insert
        if report_id not in existing_raw_map:
            existing_raw.append(report)
            new_raw_count += 1
            
    print(f"[Pipeline] Merged {new_raw_count} new raw signals. Total raw signals: {len(existing_raw)}")
    
    # Save raw reports
    save_json(existing_raw, RAW_FILE)
    
    # 4. Clean and filter reports
    print("[Pipeline] Running cleaner and deduplicator...")
    clean_reports = clean_and_filter(existing_raw)
    save_json(clean_reports, CLEAN_FILE)
    
    # 5. Label and resolve locations for ML training dataset
    print("[Pipeline] Running heuristic labeling engine...")
    labeled_dataset = label_all(clean_reports)
    save_json(labeled_dataset, TRAINING_FILE)
    
    print("="*50)
    print("Pipeline Execution Cycle Completed Successfully")
    print("="*50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Pakistan Disaster Data Ingestion & ML Dataset Pipeline")
    parser.add_argument("--once", action="store_true", help="Run the pipeline once and exit")
    parser.add_argument("--interval", type=int, default=60, help="Interval in seconds for the real-time loop (default: 60)")
    args = parser.parse_args()
    
    if args.once:
        run_pipeline_cycle()
    else:
        print(f"Starting real-time disaster ingestion loop (Interval: {args.interval}s)...")
        print("Press Ctrl+C to exit.")
        try:
            while True:
                run_pipeline_cycle()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nPipeline ingestion stopped by user.")

if __name__ == "__main__":
    main()
