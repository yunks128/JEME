#!/usr/bin/env python3
"""Capture dashboard screenshots for the journal paper.

Uses Playwright (headless Chromium) to navigate to each page and save a
PNG into figures/. Run after the React/Next dashboards are up locally:

  http://localhost:3000/science-model-dashboard/         (JEME)
  http://localhost:3000/science-model-dashboard/JEOE     (JEOE)
  http://localhost:3000/science-model-dashboard/ECCO     (model page)
  ...
  http://localhost:3002/sci-profile/                     (JESP)

Each screenshot waits 3 s after networkidle so Recharts / D3 finish
rendering. 1600×1100 viewport gives publication-friendly resolution.
"""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

OUT = Path(__file__).parent / 'figures'
OUT.mkdir(parents=True, exist_ok=True)

PAGES = [
    ('fig11_jeme_dashboard.png',
     'http://localhost:3000/science-model-dashboard/',
     'JEME main dashboard — eight Earth system models'),
    ('fig12_ecco_model.png',
     'http://localhost:3000/science-model-dashboard/ECCO',
     'ECCO model page — citations, engagement levels, geographic reach'),
    ('fig13_ecco_uncertainty.png',
     'http://localhost:3000/science-model-dashboard/ECCO/uncertainty',
     'ECCO uncertainty page — three-phase UQ pipeline outputs'),
    ('fig14_jeoe_dashboard.png',
     'http://localhost:3000/science-model-dashboard/JEOE',
     'JEOE main dashboard — three NASA observation missions'),
    ('fig15_jesp_dashboard.png',
     'http://localhost:3002/sci-profile/',
     'JESP scientist profiles — 199 researchers, collaboration network'),
]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={'width': 1600, 'height': 1100},
                                        device_scale_factor=2)  # retina
        for fname, url, caption in PAGES:
            page = await ctx.new_page()
            print(f'  capturing {fname}  <-  {url}')
            try:
                await page.goto(url, wait_until='networkidle', timeout=45000)
                # Allow charts to finish animating
                await page.wait_for_timeout(3000)
                await page.screenshot(path=str(OUT / fname), full_page=False)
            except Exception as e:
                print(f'    ERROR: {e}')
            finally:
                await page.close()
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
