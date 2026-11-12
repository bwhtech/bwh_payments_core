request_logs = []


def create_request_log(data, **kwargs):
	request_logs.append({"data": data, **kwargs})


def refuse_live_call(*args, **kwargs):
	raise AssertionError("Tests never call a live gateway")


make_get_request = make_post_request = make_put_request = make_request = refuse_live_call
