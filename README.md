# Myntra Product Scraper

## How to Run

Create a virtual environment:

```bash
python -m venv clarityenv
```

Activate it:

```bash
# Windows
.\clarityenv\Scripts\Activate.ps1

# macOS/Linux
source clarityenv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

Start the server:

```bash
uvicorn app.main:app
```

Open:

```
http://localhost:8000/docs
```

Upload a CSV containing the `product_id` column.

---

## Approach

The scraper uses **Playwright** because Myntra renders most of its data on the client side.

Instead of scraping HTML elements, I extract data from Myntra's hydration state:

- `window.__myx.pdpData` for product details
- `window.__myx.searchData` for category pages

This is much more stable than relying on CSS selectors.

A single browser instance is reused for the entire CSV to reduce overhead. If a product fails, the error is recorded and the scraper continues with the remaining products.

---

## Why NDJSON?

Results are written as **NDJSON** (one JSON object per line) instead of one large JSON array.

This allows the scraper to:

- save progress continuously,
- recover partial results if the process stops,
- avoid keeping the entire output in memory.

The file is flushed after every batch of records to minimise data loss.

---

## Assumptions

- Product pages are publicly accessible.
- Sponsored products are available in `window.__myx.searchData.results.plaProducts`.
- Category URLs can be derived from the product category.

---

## Scope

### Included

- CSV upload
- Product detail scraping
- Sponsored product scraping
- Retry and error handling
- Incremental NDJSON output

### Not Included

- Proxy rotation
- Parallel scraping
- Background jobs
- Frontend
- Database

---

## If I Had More Time

The next improvements would be:

- Move scraping to a background job and return a task ID immediately.
- Add proxy/user-agent rotation for better reliability.
- Periodically restart the browser context during long scraping sessions.
- Add job status and progress endpoints.

---

## Known Limitations

- The scraper depends on Myntra's current hydration data structure.
- Some products may fail if they are removed or temporarily unavailable.
- Processing is sequential to reduce the chance of being rate-limited.

---

## Result

**Input:** [CSV File](uploads/00214a18-a367-4bba-8df8-ed95062e4ca8.csv)

**Output:** [NDJSON file](results/00214a18-a367-4bba-8df8-ed95062e4ca8.ndjson)

```json
{"product_id":"35512522","brand":"EcoRight","title":"Eve Women Textured Crossbody Shoulder Bag","rating":4.53,"category":"Handbags","images":["...","..."],"sponsored_products":[...]}

{"product_id":"66138598","error":"Product data not found."}
```
