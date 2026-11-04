from pydantic import BaseModel, ConfigDict, model_validator


class GatewayResult(BaseModel):
	# Rejecting a numeric refund id after money moved would leave the refund unrecorded.
	model_config = ConfigDict(coerce_numbers_to_str=True)


class CheckoutSession(GatewayResult):
	session_id: str
	redirect_url: str
	success_url: str | None = None
	cancel_url: str | None = None
	failure_url: str | None = None


class RefundResult(GatewayResult):
	# All optional: read after money moved, so a thin result must not fail.
	refund_id: str | None = None
	status: str | None = None
	amount: float | None = None


class WebhookEvent(GatewayResult):
	"""A payment event carries `session_id`; a refund event carries `refund_id` instead.

	With `sync_status`, the request asks the gateway instead of applying `status`. A gateway whose
	payment still needs a capture uses it, so money moves in our own status sync, never in a guest request.
	"""

	session_id: str | None = None
	status: str
	sync_status: bool = False
	event_id: str | None = None
	refund_id: str | None = None
	# Major units. Needed to record a refund raised outside this app.
	refund_amount: float | None = None
	# The settled payment's id, which finds the request for a refund raised outside this app.
	transaction_ref: str | None = None

	@model_validator(mode="after")
	def require_session_or_refund(self):
		if not (self.session_id or self.refund_id):
			raise ValueError("A webhook event needs a session_id or a refund_id")
		return self


class GatewayOption(BaseModel):
	"""A gateway as a storefront lists it. Logos are site-relative asset paths."""

	name: str
	title: str
	logo: str | None = None
	logo_dark: str | None = None


class GatewayInfo(BaseModel):
	"""A gateway this app can take payments through, as a settings screen lists it, set up or not."""

	name: str
	settings_doctype: str
	description: str | None = None
	docs_url: str | None = None
	reusable_checkout: bool = False
	logo: str | None = None
	logo_dark: str | None = None
