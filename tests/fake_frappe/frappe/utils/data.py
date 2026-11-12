import math


def flt(s, precision=None, rounding_method=None):
	if s is None:
		return 0.0
	if isinstance(s, str):
		s = s.replace(",", "")
	try:
		num = float(s)
		if precision is not None:
			num = bankers_rounding_legacy(num, int(precision))
	except Exception:
		num = 0.0
	return num


def cint(s, default=0):
	if s is None:
		return default
	try:
		return int(s)
	except Exception:
		try:
			return int(float(s))
		except Exception:
			return default


# Frappe's default rounding method on a site with no System Settings choice.
def bankers_rounding_legacy(num, precision):
	multiplier = 10**precision
	num = round(num * multiplier if precision else num, 8)

	floor_num = math.floor(num)
	decimal_part = num - floor_num

	if not precision and decimal_part == 0.5:
		num = floor_num if (floor_num % 2 == 0) else floor_num + 1
	elif decimal_part == 0.5:
		num = floor_num + 1
	else:
		num = round(num)

	return (num / multiplier) if precision else num
