from threedi_schema.domain.models import DECLARED_MODELS

from threedi_modelchecker.config import Config

checks = Config(models=DECLARED_MODELS).checks


def test_check_descriptions():
    for check in checks:
        check_code = str(check.error_code).zfill(4)
        try:
            check.level.name.capitalize()
        except Exception as e:
            raise AssertionError(
                f"Could not capitalise level name for check {check_code}"
            ) from e
        try:
            check.description()
        except Exception as e:
            raise AssertionError(
                f"Could not generate description for check {check_code}"
            ) from e
