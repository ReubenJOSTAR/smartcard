"""Open Food Facts API client. See api/CLAUDE.md → Barcode Lookup Waterfall.

Open Food Facts has no pricing data — it only confirms what a product is
(name/brand/category). Callers must not expect a price from `lookup()`.
"""

import httpx

BASE_URL = "https://world.openfoodfacts.org/api/v2/product"
REQUEST_TIMEOUT_SECONDS = 5.0


class OpenFoodFactsClient:
    async def lookup(self, barcode: str) -> dict | None:
        params = {"fields": "product_name,brands,categories,status"}
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.get(f"{BASE_URL}/{barcode}.json", params=params)
                response.raise_for_status()
        except httpx.HTTPError:
            return None

        data = response.json()
        if data.get("status") != 1:
            return None

        product = data.get("product", {})
        name = product.get("product_name")
        if not name:
            return None

        return {"name": name, "brand": product.get("brands"), "category": product.get("categories")}
