from fastapi import FastAPI, UploadFile, File, HTTPException
from playwright.async_api import async_playwright
import pandas as pd
import asyncio
import sys

from app.scraper import scrape_product

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI()


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):

    df = pd.read_csv(file.file)
    product_ids = df["product_id"].astype(str).tolist()
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-http2",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )

        page = await context.new_page()
        await page.set_extra_http_headers(
            {"Accept-Language": "en-IN,en;q=0.9", "Upgrade-Insecure-Requests": "1"}
        )
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)

        results = []

        for product_id in product_ids:
            product = await scrape_product(page, product_id)
            print(product)
            results.append(product)

        await browser.close()

    return results
