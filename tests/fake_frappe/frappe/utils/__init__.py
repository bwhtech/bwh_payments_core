import re

from frappe.utils.data import cint, flt

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email_address(email, throw=False):
	email = (email or "").strip()
	return email if EMAIL.match(email) else ""
