import json
from pathlib import Path
from typing import List, Dict

from .ocr import OCREngine
from .offer_matching import OfferMatcher


def alert_admins(message: str, log_path: Path) -> None:
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(message + "\n")


class ReceiptProcessor:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.ocr = OCREngine()
        self.offers_path = data_dir / "offers.json"
        self.redemptions_path = data_dir / "redemptions.json"
        self.alert_log = data_dir / "admin_alerts.log"
        if not self.redemptions_path.exists():
            with open(self.redemptions_path, "w", encoding="utf-8") as f:
                json.dump([], f)
        self.matcher = OfferMatcher(self.offers_path)

    def _save_redemption(self, offer: Dict, line: str) -> None:
        with open(self.redemptions_path, "r+", encoding="utf-8") as f:
            records = json.load(f)
            records.append({"offer": offer, "line": line})
            f.seek(0)
            json.dump(records, f, indent=2)
            f.truncate()

    def process_receipt(self, image_path: Path) -> List[Dict]:
        text = self.ocr.extract_text(image_path)
        lines = [l for l in text.splitlines() if l.strip()]
        results: List[Dict] = []
        mismatches: List[str] = []
        for line in lines:
            offer = self.matcher.match_line(line)
            if offer:
                self._save_redemption(offer, line)
                results.append({"line": line, "offer": offer})
            else:
                mismatches.append(line)
                results.append({"line": line, "offer": None})
        if mismatches:
            alert_admins(
                f"Mismatched lines in {image_path.name}: {mismatches}",
                self.alert_log,
            )
        return results
