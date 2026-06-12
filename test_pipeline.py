import unittest
import datetime
from normalizer import parse_timestamp, normalize_report
from cleaner import clean_text, is_disaster_related, clean_and_filter
from labeler import resolve_location, classify_disaster, parse_magnitude, score_priority, generate_labeled_report

class TestDisasterPipeline(unittest.TestCase):

    # --- Normalizer Tests ---
    def test_parse_timestamp_usgs(self):
        # 1686564000000 ms is 2023-06-12T10:00:00Z UTC
        ts = parse_timestamp("usgs", 1686564000000)
        self.assertEqual(ts, "2023-06-12T10:00:00Z")

    def test_parse_timestamp_reddit(self):
        # 1686564000 is 2023-06-12T10:00:00Z UTC
        ts = parse_timestamp("reddit", 1686564000)
        self.assertEqual(ts, "2023-06-12T10:00:00Z")

    def test_parse_timestamp_gdelt(self):
        ts = parse_timestamp("gdelt", "20260612100000")
        self.assertEqual(ts, "2026-06-12T10:00:00Z")

    def test_parse_timestamp_reliefweb(self):
        ts = parse_timestamp("reliefweb", "2026-06-12T10:00:00+00:00")
        self.assertEqual(ts, "2026-06-12T10:00:00Z")

    # --- Cleaner Tests ---
    def test_clean_text(self):
        dirty = "<p>Flood in <b>Swat</b>! Visit https://example.com for info.</p>"
        clean = clean_text(dirty)
        self.assertEqual(clean, "Flood in Swat! Visit for info.")

    def test_is_disaster_related(self):
        self.assertTrue(is_disaster_related("There is a massive flood warning in Sindh"))
        self.assertFalse(is_disaster_related("Let's go watch a movie in Lahore today"))

    def test_clean_and_filter_deduplication(self):
        raw = [
            {"id": "1", "source": "reddit", "text": "Flood in Punjab villages", "location_text": "Punjab", "timestamp": "2026-06-12T10:00:00Z"},
            {"id": "1", "source": "reddit", "text": "Flood in Punjab villages", "location_text": "Punjab", "timestamp": "2026-06-12T10:00:00Z"}, # duplicate ID
            {"id": "2", "source": "gdelt", "text": "Flood in Punjab villages!!!", "location_text": "Pakistan", "timestamp": "2026-06-12T10:02:00Z"}, # duplicate text signature
            {"id": "3", "source": "reddit", "text": "Just posting standard daily chat here", "location_text": "Pakistan", "timestamp": "2026-06-12T10:03:00Z"} # unrelated chatter
        ]
        cleaned = clean_and_filter(raw)
        # Should only keep the first one
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned[0]["id"], "1")

    # --- Labeler Tests ---
    def test_resolve_location(self):
        self.assertEqual(resolve_location("Severe flooding in SWAT valley", "Pakistan"), "Swat, Khyber Pakhtunkhwa")
        self.assertEqual(resolve_location("Earthquake tremors felt in Peshawar today", ""), "Peshawar, Khyber Pakhtunkhwa")
        self.assertEqual(resolve_location("General disaster report", "Sindh"), "Sindh")
        self.assertEqual(resolve_location("Unknown place signal", "Global"), "Pakistan")

    def test_classify_disaster(self):
        self.assertEqual(classify_disaster("Earthquake magnitude 5.4 in northern regions"), "earthquake")
        self.assertEqual(classify_disaster("Torrential rain causing massive floods"), "flood")
        self.assertEqual(classify_disaster("Landslide blocks Karakoram Highway"), "landslide")
        self.assertEqual(classify_disaster("Storm alert issued"), "other")

    def test_parse_magnitude(self):
        self.assertEqual(parse_magnitude("USGS report: magnitude 5.2 near Quetta"), 5.2)
        self.assertEqual(parse_magnitude("An earthquake of M 4.8 hit KP"), 4.8)
        self.assertEqual(parse_magnitude("6.1 magnitude earthquake recorded"), 6.1)

    def test_score_priority(self):
        # Critical checks
        self.assertEqual(score_priority("Earthquake of magnitude 6.3 hit northern regions", "earthquake"), "critical")
        self.assertEqual(score_priority("Flash floods left 12 dead in Swat Valley", "flood"), "critical")
        self.assertEqual(score_priority("Monsoon rain sweeps away local houses in Balochistan", "flood"), "critical")
        
        # High checks
        self.assertEqual(score_priority("Earthquake of magnitude 5.5 near Islamabad", "earthquake"), "high")
        self.assertEqual(score_priority("Landslides blocked Karakoram highway causing traffic suspension", "landslide"), "high")
        
        # Medium checks
        self.assertEqual(score_priority("Monsoon rain warning issued by meteorological dept", "flood"), "medium")
        self.assertEqual(score_priority("Earthquake of M 4.2 felt in Swat", "earthquake"), "medium")
        
        # Low checks
        self.assertEqual(score_priority("Standard monsoon showers expected tomorrow", "flood"), "low")

if __name__ == "__main__":
    unittest.main()
