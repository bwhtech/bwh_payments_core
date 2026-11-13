import frappe
from frappe import _

from bwh_payments_core.engine import DEFAULT_DOCTYPES, Doctypes
from bwh_payments_core.utils import run_as_administrator


def get_return_url(return_endpoint: str | None, payment_request: str) -> str:
	if not return_endpoint:
		raise NotImplementedError("Set return_endpoint on the payment request controller to use redirect_to")
	return frappe.utils.get_url(f"{return_endpoint}?request={payment_request}")


def return_from_gateway(request: str, doctypes: Doctypes = DEFAULT_DOCTYPES):
	redirect_to = frappe.db.get_value(doctypes.payment_request, request, "redirect_to")
	if not redirect_to:
		raise frappe.DoesNotExistError(_("Payment not found"))

	payment_request = frappe.get_doc(doctypes.payment_request, request)
	# The browser's arrival proves nothing: read the status from the gateway, never the URL.
	if payment_request.status == "Pending":
		try:
			with run_as_administrator():
				payment_request.sync_status()
		except Exception:
			# The shopper still goes on; the webhook settles the payment later.
			frappe.db.rollback()
			frappe.clear_last_message()
			frappe.log_error(title=_("Could not confirm payment {0} on return").format(request))
		# Frappe rolls back GET requests; keep the gateway's answer or the error log.
		frappe.local.flags.commit = True

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = redirect_to
