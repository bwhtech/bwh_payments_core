import re
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
