# Backend / Tooling Task

## Problem Statement
We need to scrape products from Myntra (both Product Detail Pages and Category pages).

---

### Setup
1. Clone the repository and set up a virtual environment:
   ```bash
   python -m venv clarityenv
   
   # Windows (PowerShell)
   .\clarityenv\Scripts\Activate.ps1
   
   # Windows (Command Prompt)
   .\clarityenv\Scripts\Activate.bat

   # macOS/Linux
   source clarityenv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

### Running the Application
Start the FastAPI server:
```bash
uvicorn app.main:app
```
Open your browser to `http://localhost:8000/docs` to use the Swagger UI, or run a `cURL` request to upload a product CSV:
```bash
curl -X POST "http://localhost:8000/upload" -F "file=@data/products_list.csv"
```
The output will be saved inside the `results/` directory as `[UUID].ndjson`.

---

## Methodology & Architecture

* **Hydration State Extraction (`window.__myx`):** Rather than using fragile DOM/CSS selectors to parse pages, the scraper extracts data directly from Myntra's underlying hydration state JSON. This is resilient to class name updates and UI layouts.
* **FastAPI & Playwright (Async):** Playwright provides a full Chromium context to execute client-side JavaScript and bypass standard request-based bot blocking. FastAPI natively handles asynchronous requests and multipart file uploads.
* **Fault-Tolerant Scraping:** Navigation attempts retry up to 3 times. Errors on individual products are captured and recorded in the output file rather than halting the process.
* **Incremental Writes:** Records are written to the output file line-by-line and flushed periodically to prevent data loss in the event of an interruption.

---

## Core Assumptions

1. **Category Slugs:** Category page slugs correspond directly to the lowercased, hyphenated product category (e.g., `articleType` "Casual Shoes" maps to `https://www.myntra.com/casual-shoes`).
2. **Rate Limiting:** Sequential processing is preferred over parallel execution to prevent immediate blocks.
3. **Public Availability:** Products are publicly accessible and do not require user authentication.

---

## Scope Decisions

### In-Scope
- FastAPI CSV upload and parsing.
- PDP metadata extraction (Brand, Title, Description, Images, Ratings, Ratings Count).
- Category page sponsored (PLA) ads scraping (extracting up to the first 3 ads).
- Fault-tolerant, sequential loop with immediate disk flush.

### Out-of-Scope
- **Concurrency:** Multi-threaded page navigation was omitted to avoid quick rate-limit blocks.
- **Proxy Rotation:** Integration with residential proxy networks was left out to keep setup simple.
- **Web UI:** Scoped out to focus on a robust, fault-tolerant backend core.

### Future Roadmap
1. **Asynchronous Task Queue:** Return a task ID immediately on upload and process the scraping in the background to avoid HTTP timeout limits on large files.
2. **Proxy Integration:** Incorporate residential proxy pools and user-agent rotation to enable scalable, parallel crawling.
3. **Memory Recycling:** Periodically refresh the Playwright browser/context to avoid long-term memory leaks during large scrape lists.

---

## Sample Output

```json
{"product_id": "35512522", "brand": "EcoRight", "title": "Eve Women Textured Crossbody Shoulder Bag", "description": "Coffee brown textured sling bag<br>1 main compartment, has a zip closure, 2 inner pockets<br>With a detachable sling strap<br>Warranty: 6 months<br>Warranty provided by brand owner/manufacturer", "rating": 4.532258064516129, "ratings_count": 186, "category": "Handbags", "images": ["http://assets.myntassets.com/assets/images/2026/JULY/7/gDRYysJi_2ab1f01199b745e3b46dedcaa4b6eb41.jpg", "http://assets.myntassets.com/assets/images/2026/JULY/7/ZjsQlV6x_08d567e2c5304902b46a569c0b84cdb5.jpg"], "sponsored_products": [{"title": "Accessorize Women Colorblock Dorota Monogram Satchel Bag", "brand": "Accessorize", "rating": 4.239436626434326, "price": 2167, "mrp": 6995, "discount": 4828}, {"title": "Allen Solly Brand Logo Printed Structured Sling Bag", "brand": "Allen Solly", "rating": 4.589473724365234, "price": 1559, "mrp": 2599, "discount": 1040}, {"title": "Accessorize London Women's Erin Contrast Stitch Handheld Bag", "brand": "Accessorize", "rating": 4.365853786468506, "price": 1586, "mrp": 6895, "discount": 5309}]}
{"product_id": "66138598", "error": "Product data not found."}
```
