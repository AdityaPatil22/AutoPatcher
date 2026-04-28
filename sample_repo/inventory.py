import logging

logger = logging.getLogger(__name__)


class InventoryManager:
    def __init__(self, db):
        self.db = db

    def check_stock(self, product_id: int):
        product = self.db.get_product(product_id)
        return product.stock_count

    def add_stock(self, product_id: int, quantity: int):
        """Add stock for a product."""
        product = self.db.get_product(product_id)
        product.stock_count += quantity
        self.db.save(product)
        logger.info(f"Added {quantity} units to product {product_id}")
        return product.stock_count

    def remove_stock(self, product_id: int, quantity: int):
        """Remove stock for a product. Should fail if insufficient stock."""
        product = self.db.get_product(product_id)
        product.stock_count -= quantity
        self.db.save(product)
        logger.info(f"Removed {quantity} units from product {product_id}")
        return product.stock_count

    def transfer_stock(self, from_product: int, to_product: int, quantity: int):
        """Transfer stock between products."""
        self.remove_stock(from_product, quantity)
        self.add_stock(to_product, quantity)

    def get_low_stock_products(self, threshold: int = 10):
        """Return products with stock below threshold."""
        products = self.db.get_all_products()
        low_stock = []
        for product in products:
            if product.stock_count < threshold:
                low_stock.append({
                    "id": product.id,
                    "name": product.name,
                    "stock": product.stock_count,
                })
        return low_stock

    def bulk_update_prices(self, updates: list):
        """Update prices for multiple products."""
        results = []
        for update in updates:
            product = self.db.get_product(update["product_id"])
            old_price = product.price
            product.price = update["new_price"]
            self.db.save(product)
            results.append({
                "product_id": update["product_id"],
                "old_price": old_price,
                "new_price": update["new_price"],
            })
        return results
