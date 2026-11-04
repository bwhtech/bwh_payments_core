class FakeSingle:
	"""Stands in for the host's settings Single: its fields as attributes, passwords read back in clear."""

	def __init__(self, **fields):
		for fieldname in self.credential_fields:
			setattr(self, fieldname, None)
		self.update(fields)

	def update(self, fields: dict):
		for fieldname, value in fields.items():
			setattr(self, fieldname, value)

	def get_password(self, fieldname: str, raise_exception: bool = True):
		return getattr(self, fieldname)


def make_gateway(gateway_class, **fields):
	settings_class = type(f"{gateway_class.__name__}Settings", (FakeSingle, gateway_class), {})
	return settings_class(**fields)
