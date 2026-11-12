import pytest
from pydantic import ValidationError

from bwh_payments_core.contract import PaymentGatewayBase
from bwh_payments_core.models import CheckoutSession, RefundResult, WebhookEvent


class MinimalGateway(PaymentGatewayBase):
	def create_session(self, amount, currency, reference=None, customer=None, return_url=None):
		return CheckoutSession(session_id="cs_1", redirect_url="https://pay.test/cs_1")

	def get_payment_status(self, session_id):
		return "Pending"

	def refund_payment(self, session_id, amount, currency=None):
		return RefundResult()

	def handle_webhook(self, payload, headers):
		return None


def test_a_gateway_missing_a_required_method_cannot_be_built():
	class IncompleteGateway(PaymentGatewayBase):
		def create_session(self, amount, currency, reference=None, customer=None, return_url=None): ...

	with pytest.raises(TypeError):
		IncompleteGateway()


def test_a_gateway_that_skips_the_optional_methods_reports_it_cannot_answer():
	gateway = MinimalGateway()

	assert gateway.cancel_session("cs_1") is False
	assert gateway.supported_currencies() is None
	assert gateway.get_refund_status("cs_1", "re_1") is None
	assert gateway.list_refunds("cs_1") is None
	assert gateway.get_transaction_ref("cs_1") is None
	assert gateway.credential_fields == ()
	assert gateway.get_gateway_name() == "MinimalGateway"


def test_a_webhook_event_needs_a_session_or_a_refund():
	with pytest.raises(ValidationError):
		WebhookEvent(status="Paid")

	assert WebhookEvent(refund_id="re_1", status="processed").refund_id == "re_1"


def test_numeric_ids_from_a_gateway_are_read_as_text():
	refund = RefundResult.model_validate({"refund_id": 4002201, "status": "succeeded"})

	assert refund.refund_id == "4002201"


def test_a_thin_refund_result_still_validates():
	assert RefundResult.model_validate({}).refund_id is None


def test_a_gateway_that_returns_dicts_still_validates():
	session = CheckoutSession.model_validate({"session_id": "cs_1", "redirect_url": "https://pay.test/cs_1"})

	assert session.success_url is None
