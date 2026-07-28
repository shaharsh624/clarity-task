from fastapi import FastAPI, UploadFile, File
from playwright.async_api import async_playwright
import pandas as pd
import asyncio
import sys
import uuid
import json
import os
import shutil

from app.scraper import scrape_product

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI()

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):

    # Generate unique id
    file_id = str(uuid.uuid4())

    # -----------------------------
    # Save uploaded CSV
    # -----------------------------
    csv_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.csv")

    with open(csv_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Read CSV
    df = pd.read_csv(csv_path)

    product_ids = df["product_id"].astype(str).tolist()

    result_path = os.path.join(RESULT_FOLDER, f"{file_id}.ndjson")

    results = []
    batch_size = 10
    with open(result_path, "w", encoding="utf-8") as ndjson_file:

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

            for i, product_id in enumerate(product_ids, start=1):

                product = await scrape_product(page, product_id)

                results.append(product)

                # Write immediately to NDJSON
                ndjson_file.write(json.dumps(product, ensure_ascii=False) + "\n")

                # Flush every batch of 10
                if i % batch_size == 0:
                    ndjson_file.flush()
                    os.fsync(ndjson_file.fileno())

            await browser.close()

    return {
        "id": file_id,
        "csv_file": csv_path,
        "result_file": result_path,
        "total_products": len(product_ids),
        "processed_products": len(results),
        "results": results,
    }
