import json
import secrets
from types import SimpleNamespace
from typing import ClassVar

in_test = True


class ValidationError(Exception):
	pass


class AppNotInstalledError(ValidationError):
	pass


class _dict(dict):
	def __getattr__(self, key):
		return self.get(key)

	def __setattr__(self, key, value):
		self[key] = value


installed_apps = ("frappe",)
queued_jobs = []

local = SimpleNamespace(lang="en", request_ip="127.0.0.1")


class FakeDatabase:
	currencies: ClassVar[set[str]] = {"AED", "BHD", "EUR", "INR", "JPY", "KWD", "QAR", "SAR", "USD"}

	def exists(self, doctype, name=None):
		if doctype == "Currency":
			return name in self.currencies
		raise NotImplementedError(f"The fake frappe has no {doctype} table")


db = FakeDatabase()


def _(message, *args, **kwargs):
	return message


def bold(text):
	return f"<strong>{text}</strong>"


def throw(message, exc=ValidationError, title=None, **kwargs):
	raise exc(message)


def generate_hash(txt=None, length=56):
	return secrets.token_hex((length + 1) // 2)[:length]


def parse_json(value):
	if isinstance(value, str):
		value = json.loads(value)
	if isinstance(value, dict):
		value = _dict(value)
	return value


def enqueue(method, **kwargs):
	# The real job runner resolves a string through get_attr, which refuses a library's dotted path.
	if isinstance(method, str) and method.split(".", 1)[0] not in installed_apps:
		raise AppNotInstalledError(f"App {method.split('.', 1)[0]} is not installed")
	queued_jobs.append({"method": method, **kwargs})
