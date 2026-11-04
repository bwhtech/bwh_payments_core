import unittest

import frappe
import stripe
from gateways import make_gateway

from bwh_payments_core.connectors.stripe.gateway import StripeGateway
from bwh_payments_core.connectors.stripe.stub import (
	StubStripeClient,
	build_checkout_completed_event,
	build_refund_event,
	sign_payload,
)

WEBHOOK_SECRET = "whsec_test_secret"
RETURN_URL = "https://shop.test/api/method/payments.return_from_gateway?request=GPR-1"


class TestStripeGateway(unittest.TestCase):
	def setUp(self):
		StubStripeClient.reset()
		self.settings = make_gateway(
			StripeGateway,
			private_key="sk_test_x",
			webhook_secret=WEBHOOK_SECRET,
			success_url="https://shop.test/en/account/orders/confirmation",
			failure_url="https://shop.test/en/cart/checkout",
		)

	def get_charged_amount(self):
		return StubStripeClient.created_sessions[-1]["line_items"][0]["price_data"]["unit_amount"]

	def test_success_url_keeps_the_stripe_placeholder_and_existing_query(self):
		self.settings.success_url = "https://shop.test/en/confirm?ref=abc"

		success_url = self.settings.build_success_url()

		self.assertIn("ref=abc", success_url)
		self.assertIn("session_id={CHECKOUT_SESSION_ID}", success_url)
		self.assertEqual(success_url.count("?"), 1)

	def test_a_missing_success_url_is_refused(self):
		self.settings.success_url = ""

		with self.assertRaises(frappe.ValidationError):
			self.settings.create_session(100, "USD", reference="GPR-1")

		self.assertEqual(StubStripeClient.created_sessions, [])

	def test_stripe_sends_the_shopper_back_to_the_given_return_url_either_way(self):
		self.settings.success_url = ""

		self.settings.create_session(100, "SAR", reference="GPR-1", return_url=RETURN_URL)

		created = StubStripeClient.created_sessions[-1]
		self.assertEqual((created["success_url"], created["cancel_url"]), (RETURN_URL, RETURN_URL))

	def test_create_session_charges_iso_minor_units(self):
		self.settings.create_session(12.345, "KWD", reference="GPR-1")
		self.assertEqual(self.get_charged_amount(), 12345)

		self.settings.create_session(1500, "JPY", reference="GPR-2")
		self.assertEqual(self.get_charged_amount(), 1500)

	def test_an_unknown_currency_is_refused_before_any_call(self):
		with self.assertRaises(frappe.ValidationError):
			self.settings.create_session(100, "XYZ", reference="GPR-1")

		self.assertEqual(StubStripeClient.created_sessions, [])

	def test_the_session_id_is_the_one_status_reads_and_webhooks_use(self):
		session = self.settings.create_session(100, "USD", reference="GPR-1")

		self.assertEqual(self.settings.get_payment_status(session.session_id), "Pending")
		StubStripeClient.pay(session.session_id)
		self.assertEqual(self.settings.get_payment_status(session.session_id), "Paid")
		self.assertEqual(self.settings.get_transaction_ref(session.session_id), f"pi_{session.session_id}")

	def test_an_open_session_is_expired_and_a_paid_one_is_not(self):
		open_session = self.settings.create_session(100, "USD", reference="GPR-1").session_id
		paid_session = self.settings.create_session(100, "USD", reference="GPR-2").session_id
		StubStripeClient.pay(paid_session)

		self.assertTrue(self.settings.cancel_session(open_session))
		self.assertEqual(self.settings.get_payment_status(open_session), "Expired")
		self.assertFalse(self.settings.cancel_session(paid_session))
		self.assertEqual(self.settings.get_payment_status(paid_session), "Paid")

	def test_a_paid_session_refunds_in_minor_units_and_reports_major_units(self):
		session_id = self.settings.create_session(12.345, "KWD", reference="GPR-1").session_id
		StubStripeClient.pay(session_id)

		refund = self.settings.refund_payment(session_id, 10.5, "KWD")

		self.assertEqual(
			StubStripeClient.created_refunds[-1], {"payment_intent": f"pi_{session_id}", "amount": 10500}
		)
		self.assertEqual((refund.status, refund.amount), ("succeeded", 10.5))

	def test_an_unpaid_session_is_never_refunded(self):
		session_id = self.settings.create_session(100, "USD", reference="GPR-1").session_id

		with self.assertRaises(frappe.ValidationError):
			self.settings.refund_payment(session_id, 100, "USD")

		self.assertEqual(StubStripeClient.created_refunds, [])

	def test_a_refund_stripe_reports_failed_throws(self):
		session_id = self.settings.create_session(100, "USD", reference="GPR-1").session_id
		StubStripeClient.pay(session_id)
		StubStripeClient.next_refund_status = "failed"

		with self.assertRaises(frappe.ValidationError):
			self.settings.refund_payment(session_id, 100, "USD")

	def test_a_pending_refund_reads_its_new_status_back(self):
		session_id = self.settings.create_session(100, "USD", reference="GPR-1").session_id
		StubStripeClient.pay(session_id)
		StubStripeClient.next_refund_status = "pending"
		refund = self.settings.refund_payment(session_id, 40, "USD")
		StubStripeClient.set_refund_status(refund.refund_id, "succeeded")

		self.assertEqual(self.settings.get_refund_status(session_id, refund.refund_id).status, "succeeded")


class TestStripeWebhook(unittest.TestCase):
	def setUp(self):
		self.settings = make_gateway(StripeGateway, webhook_secret=WEBHOOK_SECRET)

	def handle(self, payload: bytes, signature: str | None):
		headers = {"Stripe-Signature": signature} if signature is not None else {}
		return self.settings.handle_webhook(payload, headers)

	def test_a_signed_completed_checkout_is_paid(self):
		payload = build_checkout_completed_event("cs_test_1", event_id="evt_1")

		event = self.handle(payload, sign_payload(payload, WEBHOOK_SECRET))

		self.assertEqual((event.session_id, event.status, event.event_id), ("cs_test_1", "Paid", "evt_1"))

	def test_a_forged_signature_is_rejected(self):
		payload = build_checkout_completed_event("cs_test_1")

		with self.assertRaises(stripe.SignatureVerificationError):
			self.handle(payload, sign_payload(payload, "attacker_guess"))

	def test_a_missing_signature_or_secret_is_rejected(self):
		payload = build_checkout_completed_event("cs_test_1")

		with self.assertRaises(frappe.ValidationError):
			self.handle(payload, None)

		self.settings.webhook_secret = ""
		with self.assertRaises(frappe.ValidationError):
			self.handle(payload, sign_payload(payload, WEBHOOK_SECRET))

	def test_a_refund_event_carries_the_refund_in_major_units_and_its_payment(self):
		payload = build_refund_event("re_1", "pi_1", "succeeded", 10500, "kwd")

		event = self.handle(payload, sign_payload(payload, WEBHOOK_SECRET))

		self.assertEqual(
			(event.refund_id, event.status, event.refund_amount, event.transaction_ref),
			("re_1", "succeeded", 10.5, "pi_1"),
		)

	def test_an_event_we_do_not_act_on_is_ignored(self):
		payload = b'{"id": "evt_2", "type": "customer.created", "data": {"object": {"id": "cus_1"}}}'

		self.assertIsNone(self.handle(payload, sign_payload(payload, WEBHOOK_SECRET)))
