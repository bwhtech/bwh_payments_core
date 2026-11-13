import frappe
from frappe import _
from frappe.utils.data import flt

from bwh_payments_core.engine import DEFAULT_DOCTYPES, Doctypes
from bwh_payments_core.models import RefundResult

REFUND_STATUS_MAP = {
	"succeeded": "Processed",
	"processed": "Processed",
	"pending": "Pending",
	"failed": "Failed",
	"canceled": "Failed",
	"cancelled": "Failed",
}


def normalise_refund_status(status: str | None) -> str:
	# A gateway that answers without a status answers only once the refund went through.
	if not status:
		return "Processed"
	return REFUND_STATUS_MAP.get(status.strip().casefold(), "Pending")


class GatewayRefundMixin:
	doctypes: Doctypes = DEFAULT_DOCTYPES

	def validate(self):
		# A refund the gateway reports without an amount must not be recorded as zero.
		if flt(self.amount) <= 0:
			frappe.throw(_("Refund amount must be greater than zero"))

	def on_update(self):
		if not self.has_value_changed("status"):
			return

		payment_request = frappe.get_doc(self.doctypes.payment_request, self.payment_request)
		if self.status == "Processed":
			payment_request.add_processed_refund(self)

		# An import records history the referenced document already reflects.
		if self.flags.imported:
			return
		frappe.get_doc(payment_request.ref_doctype, payment_request.ref_docname).run_method(
			"on_refund_update", self
		)

	def lock_row(self):
		frappe.db.get_value(self.doctype, self.name, "status", for_update=True)
		# A plain reload reads this transaction's REPEATABLE READ snapshot, which can predate the lock.
		self.flags.for_update = True
		self.reload()

	def apply_gateway_result(self, result: RefundResult):
		self.refund_id = result.refund_id or self.refund_id
		self.status = normalise_refund_status(result.status)
		self.save(ignore_permissions=True)

	def apply_gateway_status(self, status: str | None, event_id: str | None = None) -> bool:
		self.lock_row()

		status = normalise_refund_status(status)
		if event_id and self.last_webhook_event_id == event_id:
			return False
		if self.status != "Pending" or status == "Pending":
			return False

		self.status = status
		self.last_webhook_event_id = event_id
		self.save(ignore_permissions=True)
		return True

	def mark_failed(self, error: str):
		self.status = "Failed"
		self.error = error
		self.save(ignore_permissions=True)
