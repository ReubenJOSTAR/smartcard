"""Barcode lookup waterfall (DB → Open Food Facts → manual) — placeholder.
See progress.md → Backend — Products and api/CLAUDE.md → Barcode Lookup Waterfall.
"""


class ProductService:
    async def lookup_product(self, barcode: str, store_id: int | None) -> dict | None:
        ...
