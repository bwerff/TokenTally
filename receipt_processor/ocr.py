import subprocess
from pathlib import Path


class OCREngine:
    """Simple wrapper around the `tesseract` CLI."""

    def extract_text(self, image_path: Path) -> str:
        try:
            result = subprocess.run(
                ["tesseract", str(image_path), "stdout"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except Exception:
            # Environment may not have tesseract. Fail gracefully.
            return ""
