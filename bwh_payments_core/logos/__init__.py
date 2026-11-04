from pathlib import Path

LOGO_DIRECTORY = Path(__file__).parent


def get_logo_path(file_name: str) -> Path:
	path = LOGO_DIRECTORY / file_name
	if path.suffix != ".svg" or path.parent != LOGO_DIRECTORY or not path.is_file():
		raise FileNotFoundError(f"bwh_payments_core ships no logo named {file_name}")
	return path
