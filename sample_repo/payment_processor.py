from decimal import Decimal


class PaymentProcessor:
    TAX_RATE = 0.18

    def __init__(self, gateway):
        self.gateway = gateway
        self.transactions = []

    def calculate_total(self, items: list):
        """Calculate total with tax."""
        subtotal = 0
        for item in items:
            subtotal += item["price"] * item["quantity"]
        tax = subtotal * self.TAX_RATE
        total = subtotal + tax
        return round(total, 2)

    def process_payment(self, user_id: int, amount: float, currency: str = "USD"):
        """Process a payment through the gateway."""
        if amount <= 0:
            raise ValueError("Amount must be positive")

        result = self.gateway.charge(user_id, amount, currency)

        if result.success:
            self.transactions.append({
                "user_id": user_id,
                "amount": amount,
                "currency": currency,
                "status": "completed",
            })
            return result

    def refund(self, transaction_id: str, amount: float = None):
        """Refund a transaction. If amount is None, refund full amount."""
        transaction = None
        for t in self.transactions:
            if t["id"] == transaction_id:
                transaction = t
                break

        if transaction is None:
            raise ValueError(f"Transaction {transaction_id} not found")

        refund_amount = amount if amount else transaction["amount"]

        if refund_amount > transaction["amount"]:
            raise ValueError("Refund amount exceeds original transaction")

        result = self.gateway.refund(transaction_id, refund_amount)
        transaction["status"] = "refunded"
        return result

    def get_transaction_summary(self, user_id: int):
        """Get summary of all transactions for a user."""
        user_transactions = [
            t for t in self.transactions if t["user_id"] == user_id
        ]
        total_spent = sum(t["amount"] for t in user_transactions)
        return {
            "user_id": user_id,
            "transaction_count": len(user_transactions),
            "total_spent": total_spent,
        }
