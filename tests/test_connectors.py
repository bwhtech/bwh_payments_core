import ast
import inspect

import pytest
from gateways import make_gateway

from bwh_payments_core.connectors.razorpay.gateway import RazorpayGateway
from bwh_payments_core.connectors.razorpay.stub import StubRazorpayClient
from bwh_payments_core.connectors.stripe.gateway import StripeGateway
from bwh_payments_core.connectors.stripe.stub import StubStripeClient
from bwh_payments_core.connectors.tabby.gateway import TabbyGateway
from bwh_payments_core.connectors.tabby.stub import StubTabbyClient
from bwh_payments_core.connectors.telr.gateway import TelrGateway
from bwh_payments_core.connectors.telr.stub import StubTelrClient
from bwh_payments_core.logos import get_logo_path

GATEWAYS = {
	StripeGateway: StubStripeClient,
	RazorpayGateway: StubRazorpayClient,
	TelrGateway: StubTelrClient,
	TabbyGateway: StubTabbyClient,
}
# Provided by the host's Document, not by a field.
HOST_METHODS = {"get_password"}


def get_fields_read(gateway_class) -> set[str]:
	"""Every `self.<field>` and `self.get_password("<field>")` the connector reads that it does not define."""
	tree = ast.parse(inspect.getsource(inspect.getmodule(gateway_class)))
	fields = set()
	for node in ast.walk(tree):
		if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
			if not hasattr(gateway_class, node.attr) and node.attr not in HOST_METHODS:
				fields.add(node.attr)
		if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "get_password":
			fields.add(node.args[0].value)
	return fields


@pytest.mark.parametrize("gateway_class", GATEWAYS)
def test_credential_fields_name_every_field_the_connector_reads(gateway_class):
	assert get_fields_read(gateway_class) == set(gateway_class.credential_fields)


@pytest.mark.parametrize(("gateway_class", "stub_class"), GATEWAYS.items())
def test_tests_always_get_the_stub_client(gateway_class, stub_class):
	assert isinstance(make_gateway(gateway_class).get_client(), stub_class)


@pytest.mark.parametrize("gateway_class", GATEWAYS)
def test_every_connector_describes_itself_for_a_settings_screen(gateway_class):
	assert gateway_class.label == make_gateway(gateway_class).get_gateway_name()
	assert gateway_class.description
	assert gateway_class.docs_url.startswith("https://")


def test_a_connector_logo_ships_with_the_package():
	assert get_logo_path(RazorpayGateway.logo_file).read_text().lstrip().startswith("<?xml")
	assert get_logo_path(RazorpayGateway.logo_dark_file).is_file()


@pytest.mark.parametrize("file_name", ["missing.svg", "../__init__.py", "__init__.py"])
def test_only_a_shipped_svg_is_served_as_a_logo(file_name):
	with pytest.raises(FileNotFoundError):
		get_logo_path(file_name)
