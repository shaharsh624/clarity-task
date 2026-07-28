from playwright.async_api import Page
from urllib.parse import quote


async def scrape_product(page: Page, product_id: str):
    """
    Scrape a single Myntra product using its product ID.
    """

    url = f"https://www.myntra.com/{product_id}"

    try:
        # 3 attempts for a page
        for attempt in range(3):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                break
            except Exception:
                if attempt == 1:
                    raise

        data = await page.evaluate("window.__myx?.pdpData")

        if not data:
            raise Exception("Product data not found.")

        # ---------------------------
        # Brand
        # ---------------------------
        brand = data.get("brand", {}).get("name")

        # ---------------------------
        # Title
        # ---------------------------
        title = data.get("name", "")

        if brand and title.startswith(brand):
            title = title.replace(brand, "", 1).strip()

        # ---------------------------
        # Description
        # ---------------------------
        description = None

        descriptors = data.get("descriptors", [])
        if descriptors:
            description = descriptors[0].get("description")

        # ---------------------------
        # Images
        # ---------------------------
        images = []

        albums = data.get("media", {}).get("albums", [])

        if albums:

            first_album = albums[0]

            for image in first_album.get("images", [])[:2]:

                image_url = image.get("imageURL")

                if image_url:
                    images.append(image_url)

        # ---------------------------
        # Rating
        # ---------------------------
        ratings = data.get("ratings", {})

        rating = ratings.get("averageRating")
        ratings_count = ratings.get("totalCount")

        # ---------------------------
        # Category
        # ---------------------------
        analytics = data.get("analytics", {})

        category = analytics.get("articleType")

        # Category Ads
        ads = await scrape_category_ads(page, category)

        # ---------------------------
        # Return
        # ---------------------------
        return {
            "product_id": product_id,
            "brand": brand,
            "title": title,
            "description": description,
            "rating": rating,
            "ratings_count": ratings_count,
            "category": category,
            "images": images,
            "sponsored_products": ads,
        }

    except Exception as e:

        return {"product_id": product_id, "error": str(e)}


async def scrape_category_ads(page: Page, category: str):
    """
    Scrape first 3 sponsored (PLA) products from a category page.
    """

    url = f"https://www.myntra.com/{quote(category.lower().replace(' ', '-'))}"

    await page.goto(url, wait_until="domcontentloaded", timeout=60000)

    data = await page.evaluate("window.__myx?.searchData")

    if not data:
        return []

    results = data.get("results", {})
    pla_products = results.get("plaProducts", [])

    ads = []

    for product in pla_products[:3]:

        ads.append(
            {
                "title": product.get("productName"),
                "brand": product.get("brand"),
                "rating": product.get("rating"),
                "price": product.get("price"),
                "mrp": product.get("mrp"),
                "discount": product.get("discount"),
            }
        )

    return ads
