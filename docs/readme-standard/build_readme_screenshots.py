"""Take the six 800x500 grid screenshots from the demo dashboard.

Run from the repo root after `python demo/generate_demo_data.py` and
`python core/build_dashboard.py`:
    python docs/readme-standard/build_readme_screenshots.py
Needs playwright and the preinstalled Chromium. Demo data only, all companies fictional.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / "data" / "dashboard.html").as_uri()
OUT = ROOT / "docs" / "screenshots" / "grid"
CHROME = "/opt/pw-browsers/chromium"


def tab(page, name):
    page.click(f'button.nav[data-tab="{name}"]')
    page.wait_for_timeout(500)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            browser = p.chromium.launch(executable_path=CHROME)
        ctx = browser.new_context(viewport={"width": 1280, "height": 800},
                                  color_scheme="dark", device_scale_factor=1)
        page = ctx.new_page()
        page.goto(PAGE)
        page.wait_for_timeout(800)

        def shot(name):
            page.screenshot(path=str(OUT / f"{name}.png"))

        shot("overview")
        tab(page, "inbox")
        shot("inbox")
        tab(page, "search")
        shot("search-radar")
        tab(page, "jobs")
        shot("all-jobs")
        # job detail panel: open the first job in the list
        page.evaluate("openJob(DATA.jobs[0].id)")
        page.wait_for_timeout(1200)
        shot("job-detail")
        page.evaluate("document.getElementById('ovl').click()")
        page.wait_for_timeout(400)
        # light theme, overview
        page.emulate_media(color_scheme="light")
        page.evaluate("document.documentElement.dataset.theme='light'")
        tab(page, "home")
        shot("overview-light")
        browser.close()

    from PIL import Image
    for f in OUT.glob("*.png"):
        im = Image.open(f).convert("RGB")
        assert im.size == (1280, 800), im.size
        im.resize((800, 500), Image.LANCZOS).save(f, optimize=True)
    print("wrote", sorted(f.name for f in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
