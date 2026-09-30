"""Record docs/images/dashboard-tour.gif from the built demo dashboard.

Uses only the fictional demo data. Steps:
  python demo/generate_demo_data.py --force
  python core/build_dashboard.py
  python docs/readme/record_tour.py          (needs: pip install playwright pillow; a Chromium)

Set CHROMIUM to a browser executable if Playwright's own download isn't installed.
"""
import os
import sys
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "data" / "dashboard.html"
OUT = ROOT / "docs" / "images" / "dashboard-tour.gif"
W, H = 1100, 620
HOLD = [1800, 1800, 2000, 2000, 1800]   # ms per step

CAPTION_JS = """t => {
  let d = document.getElementById('__cap');
  if (!d) { d = document.createElement('div'); d.id = '__cap';
    d.style.cssText = 'position:fixed;left:50%;bottom:14px;transform:translateX(-50%);z-index:99999;background:#2e1065;color:#ede9fe;border:1px solid #a78bfa;border-radius:999px;padding:6px 18px;font:600 15px Segoe UI,Helvetica,Arial,sans-serif';
    document.body.appendChild(d); }
  d.textContent = t; }"""


def main():
    tmp = Path(tempfile.mkdtemp())
    frames = []
    with sync_playwright() as p:
        exe = os.environ.get("CHROMIUM")
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = browser.new_context(viewport={"width": W, "height": H}, color_scheme="dark",
                                   permissions=["clipboard-read", "clipboard-write"]).new_page()
        page.goto(HTML.as_uri())
        page.wait_for_timeout(1500)

        def shot(caption):
            page.evaluate(CAPTION_JS, caption)
            page.wait_for_timeout(350)
            f = tmp / f"{len(frames)}.png"
            page.screenshot(path=str(f))
            frames.append(f)

        shot("1 Overview")
        page.click('#rail button[data-tab="jobs"]')
        page.wait_for_timeout(700)
        page.fill("#fSearch", "data")
        page.wait_for_timeout(700)
        shot("2 Filter")
        page.click('article.row:has-text("Contoso")')
        page.wait_for_timeout(900)
        shot("3 Job detail")
        page.click("#dPrep")
        page.wait_for_timeout(500)
        shot("4 Copy the prompt")
        page.click("#dClose")
        page.wait_for_timeout(500)
        page.fill("#fSearch", "")
        page.click('#rail button[data-tab="home"]')
        page.wait_for_timeout(3200)
        shot("5 Back to the overview")
        browser.close()

    imgs = []
    for f in frames:
        im = Image.open(f).convert("RGB")
        im = im.resize((960, round(H * 960 / W)), Image.LANCZOS)
        imgs.append(im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    imgs[0].save(OUT, save_all=True, append_images=imgs[1:], duration=HOLD[:len(imgs)], loop=0, optimize=True)
    print("OK", OUT, OUT.stat().st_size // 1024, "KB", len(imgs), "frames")
    if os.environ.get("KEEP_FRAMES"):
        for i, f in enumerate(frames):
            Path(os.environ["KEEP_FRAMES"], f"{i}.png").write_bytes(f.read_bytes())


if __name__ == "__main__":
    sys.exit(main())
