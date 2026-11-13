from dataclasses import dataclass


@dataclass(frozen=True)
class Doctypes:
	payment_request: str = "Gateway Payment Request"
	refund: str = "Gateway Refund"
	profile: str = "Payment Gateway Profile"


DEFAULT_DOCTYPES = Doctypes()
