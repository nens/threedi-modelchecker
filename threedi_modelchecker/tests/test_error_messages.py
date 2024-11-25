from threedi_schema.domain.models import DECLARED_MODELS
from threedi_modelchecker.config import Config

checks = Config(models=DECLARED_MODELS).checks


def test_error_description():
    ordered_checks = sorted(checks, key=lambda k: (k.error_code, k.description()))

    for check in ordered_checks:
        check_code = str(check.error_code).zfill(4)
        try:
            check.level.name.capitalize()
        except Exception as e:
            raise ValueError(f"Could not capitalise level name for check {check_code}") from e
        try:
            check.description()
        except Exception as e:
            raise ValueError(f"Could not generate description for check {check_code}") from e
