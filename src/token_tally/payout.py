import base64
import json
import urllib.request
import urllib.parse
from typing import Optional

from .ledger import Ledger

STRIPE_API_URL = "https://api.stripe.com/v1/payouts"


class StripePayoutClient:
    """Handles payouts via Stripe API using basic HTTP requests."""

    def __init__(self, api_key: str, ledger: Optional[Ledger] = None):
        self.api_key = api_key
        self.ledger = ledger or Ledger()

    def create_payout(
        self, payout_id: str, user_id: str, amount: int, currency: str
    ) -> dict:
        data = urllib.parse.urlencode(
            {
                "amount": amount,
                "currency": currency,
                "metadata[user_id]": user_id,
            }
        ).encode()
        req = urllib.request.Request(STRIPE_API_URL, data=data)
        auth_header = base64.b64encode(f"{self.api_key}:".encode()).decode()
        req.add_header("Authorization", f"Basic {auth_header}")
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read())
        self.ledger.add_payout(
            payout_id=resp_data["id"],
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=resp_data.get("status", "unknown"),
            processor="stripe",
        )
        return resp_data

    def retrieve_payout(self, payout_id: str) -> dict:
        url = f"{STRIPE_API_URL}/{payout_id}"
        req = urllib.request.Request(url)
        auth_header = base64.b64encode(f"{self.api_key}:".encode()).decode()
        req.add_header("Authorization", f"Basic {auth_header}")
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read())
        self.ledger.update_status(payout_id, resp_data.get("status", "unknown"))
        return resp_data


class PayoutService:
    """Simple helper to record payouts in ``ledger.db`` and track status."""

    def __init__(self, ledger: Optional[Ledger] = None):
        self.ledger = ledger or Ledger()

    def record_payout(
        self,
        payout_id: str,
        user_id: str,
        amount: int,
        currency: str,
        processor: str = "manual",
        status: str = "pending",
    ) -> None:
        """Add a payout entry to the ledger."""
        self.ledger.add_payout(
            payout_id=payout_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=status,
            processor=processor,
        )

    def update_status(self, payout_id: str, status: str) -> None:
        """Update payout status in the ledger."""
        self.ledger.update_status(payout_id, status)

    def get_status(self, payout_id: str) -> Optional[str]:
        """Return the current status of a payout or ``None`` if unknown."""
        record = self.ledger.get_payout(payout_id)
        if record:
            return record.get("status")
        return None
