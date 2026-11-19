"""
Regenerates the profile SVG cards.
Current version keeps the cards self-contained and safe for GitHub README rendering.
Contribution data is intentionally not fabricated; connect a verified data source before
publishing numerical activity claims.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

def main():
    required = [
        ROOT / "cards/hero.svg",
        ROOT / "cards/build.svg",
        ROOT / "cards/brand.svg",
        ROOT / "cards/learn.svg",
        ROOT / "cards/activity.svg",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing cards: " + ", ".join(missing))
    print("Profile cards are present. No unverified GitHub statistics were generated.")

if __name__ == "__main__":
    main()
