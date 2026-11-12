from abc import ABC, abstractmethod

from bwh_payments_core.models import CheckoutSession, RefundResult, WebhookEvent


class PaymentGatewayBase(ABC):
	"""Contract for every `<Gateway> Gateway Settings` Single. Amounts are in major units (12.34)."""

	label: str | None = None
	# Fieldnames the host's Single must define; secrets among them are Password fields.
	credential_fields: tuple[str, ...] = ()
	logo: str | None = None
	logo_dark: str | None = None
	# SVG file names shipped with this package (see `bwh_payments_core.logos`); the host decides the served path.
	logo_file: str | None = None
	logo_dark_file: str | None = None
	# One line for a merchant choosing a gateway, and where they find its credentials.
	description: str | None = None
	docs_url: str | None = None
	# The checkout link stays payable after the shopper leaves it, so a caller can send them back to it.
	reusable_checkout: bool = False

	@abstractmethod
	def create_session(
		self,
		amount: float,
		currency: str,
		reference: str | None = None,
		customer: dict | None = None,
		return_url: str | None = None,
	) -> CheckoutSession:
		"""With `return_url`, every way back from the checkout (paid, failed, cancelled) goes there."""

	@abstractmethod
	def get_payment_status(self, session_id: str) -> str:
		"""Return a Gateway Payment Request `status` value."""

	@abstractmethod
	def refund_payment(self, session_id: str, amount: float, currency: str | None = None) -> RefundResult: ...

	@abstractmethod
	def handle_webhook(self, payload: bytes, headers: dict) -> WebhookEvent | None:
		"""Verify the signature, then return the event, or None to ignore the delivery."""

	def cancel_session(self, session_id: str) -> bool:
		return False

	def supported_currencies(self) -> tuple[str, ...] | None:
		"""ISO codes this gateway can charge in, or None for any currency the site has."""
		return None

	def get_refund_status(self, session_id: str, refund_id: str) -> RefundResult | None:
		"""What the gateway now says about a refund, or None when it cannot be asked."""
		return None

	def list_refunds(self, session_id: str) -> list[RefundResult] | None:
		"""Every refund the gateway holds for the payment, or None when it cannot list them."""
		return None

	def get_transaction_ref(self, session_id: str) -> str | None:
		"""The gateway's id for the settled payment, or None when it cannot say."""
		return None

	def get_gateway_name(self) -> str:
		return self.__class__.__name__
