import importlib

import pytest

from bwh_payments_core.engine import webhook
from bwh_payments_core.engine.checkout import get_return_url
from bwh_payments_core.engine.payment_request import GatewayPaymentRequestMixin
from bwh_payments_core.engine.refund import normalise_refund_status


@pytest.mark.parametrize(
	("gateway_status", "status"),
	[
		("succeeded", "Processed"),
		(" Processed ", "Processed"),
		("pending", "Pending"),
		("failed", "Failed"),
		("canceled", "Failed"),
		("cancelled", "Failed"),
		("who_knows", "Pending"),
		(None, "Processed"),
		("", "Processed"),
	],
)
def test_a_gateway_refund_status_is_normalised_to_ours(gateway_status, status):
	assert normalise_refund_status(gateway_status) == status


def test_the_return_url_goes_through_the_hosts_endpoint():
	assert (
		get_return_url("/api/method/shop.return", "GPR-1")
		== "https://shop.test/api/method/shop.return?request=GPR-1"
	)


def test_a_host_that_sets_no_return_endpoint_cannot_build_a_return_url():
	with pytest.raises(NotImplementedError):
		get_return_url(GatewayPaymentRequestMixin.return_endpoint, "GPR-1")


def test_the_queued_webhook_job_path_resolves(monkeypatch):
	queued = {}
	monkeypatch.setattr(
		webhook.frappe, "enqueue", lambda method, **kwargs: queued.update(method=method), raising=False
	)

	webhook.enqueue_webhook("IR-1")

	module_path, function_name = queued["method"].rsplit(".", 1)
	assert getattr(importlib.import_module(module_path), function_name) is webhook.process_webhook
