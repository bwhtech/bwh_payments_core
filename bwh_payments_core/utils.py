import re
from contextlib import contextmanager
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import frappe

LANGUAGE_SEGMENT = re.compile(r"^[a-z]{2}(-[A-Za-z]{2})?$")


def get_localised_url(url: str) -> str:
	language = frappe.local.lang
	if not (url and language):
		return url

	parts = urlsplit(url)
	segments = parts.path.split("/")
	if len(segments) < 2 or not LANGUAGE_SEGMENT.match(segments[1]) or segments[1] == language:
		return url

	segments[1] = language
	return urlunsplit((parts.scheme, parts.netloc, "/".join(segments), parts.query, parts.fragment))


def add_reference_id(url: str, reference: str | None) -> str:
	"""Localise a return URL and append `reference_id`, which storefronts read to find the request."""
	parts = urlsplit(get_localised_url(url))
	query = [*parse_qsl(parts.query), ("reference_id", reference or "")]
	return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


@contextmanager
def run_as_administrator():
	"""Settling an order downstream needs a real user. Restored after, so a worker does not stay Administrator.

	`set_user` overwrites the session's sid and data, and a web request saves that session back when it
	ends, so the whole session is restored in place. Otherwise a signed-in shopper is logged out.
	"""
	session = frappe._dict(frappe.local.session)
	try:
		frappe.set_user("Administrator")
		yield
	finally:
		frappe.set_user(session.user)
		frappe.local.session.update(session)


def is_local_path(url: str | None) -> bool:
	"""A path on this site. Browsers read `//host` and `/\\host` as another site."""
	if not url or not url.startswith("/") or url.startswith(("//", "/\\")):
		return False
	parts = urlsplit(url)
	return not (parts.scheme or parts.netloc)
