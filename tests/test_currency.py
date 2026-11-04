import frappe
import pytest

from bwh_payments_core.currency import (
	from_minor_units,
	get_minor_unit_exponent,
	to_minor_units,
	validate_transaction_currency,
)


@pytest.mark.parametrize(
	("amount", "currency", "minor_units"),
	[(12.34, "USD", 1234), (12.345, "KWD", 12345), (1234, "JPY", 1234), (19.99, "EUR", 1999)],
)
def test_amounts_convert_at_the_iso_exponent_not_the_currency_doctype(amount, currency, minor_units):
	assert to_minor_units(amount, currency) == minor_units


@pytest.mark.parametrize(
	("minor_units", "currency", "amount"), [(1234, "USD", 12.34), (12345, "BHD", 12.345), (500, "JPY", 500)]
)
def test_minor_units_read_back_to_major_units(minor_units, currency, amount):
	assert from_minor_units(minor_units, currency) == amount


def test_a_currency_code_is_matched_without_case_or_padding():
	assert get_minor_unit_exponent(" kwd ") == 3


def test_an_amount_with_no_currency_is_refused():
	with pytest.raises(frappe.ValidationError):
		to_minor_units(10, "")


def test_a_currency_the_site_does_not_have_is_refused():
	validate_transaction_currency("USD")

	with pytest.raises(frappe.ValidationError):
		validate_transaction_currency("XYZ")
