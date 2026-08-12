from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path(r"C:\Users\brive\AppData\Local\Temp\bryan_demo_sync\command-center-demo\docs\screenshots")
out.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://127.0.0.1:5055/", wait_until="networkidle")

    page.screenshot(path=str(out / "01-vault.png"), full_page=False)

    page.click("button[data-tab='review']")
    page.wait_for_timeout(400)
    page.screenshot(path=str(out / "02-code-review.png"), full_page=False)

    # Sign off first enabled patient
    signoffs = page.locator("button:has-text('Sign off + post'):not([disabled])")
    if signoffs.count() > 0:
        signoffs.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)

    page.click("button[data-tab='review']")
    page.wait_for_timeout(300)
    sim = page.locator("button:has-text('Simulate PM Approved'):not([disabled])")
    if sim.count() > 0:
        sim.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)

    page.click("button[data-tab='archive']")
    page.wait_for_timeout(400)
    page.screenshot(path=str(out / "03-archive.png"), full_page=False)

    page.click("button[data-tab='office']")
    page.wait_for_timeout(400)
    page.screenshot(path=str(out / "04-office.png"), full_page=False)

    page.click("button[data-tab='audit']")
    page.wait_for_timeout(400)
    page.screenshot(path=str(out / "05-audit.png"), full_page=False)

    page.click("button[data-tab='review']")
    page.wait_for_timeout(300)
    page.screenshot(path=str(out / "02b-code-review-after-signoff.png"), full_page=False)

    browser.close()

for path in sorted(out.glob("*.png")):
    print(f"{path.name}\t{path.stat().st_size}")
