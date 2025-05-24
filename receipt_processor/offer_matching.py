import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional


class OfferMatcher:
    def __init__(self, offers_path: Path):
        with open(offers_path, "r", encoding="utf-8") as f:
            self.offers: List[Dict] = json.load(f)

    def match_line(self, line: str) -> Optional[Dict]:
        line = line.strip()
        if not line:
            return None
        # Match by UPC first
        digits = ''.join(ch for ch in line if ch.isdigit())
        if digits:
            for offer in self.offers:
                if offer.get("upc") and offer["upc"] in digits:
                    return offer
        # Fallback to fuzzy text match
        best_offer = None
        best_ratio = 0.0
        for offer in self.offers:
            ratio = SequenceMatcher(None, offer.get("name", "").lower(), line.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_offer = offer
        if best_ratio > 0.7:
            return best_offer
        return None
