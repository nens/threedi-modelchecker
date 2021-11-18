from threedi_modelchecker.checks.patterns import TIMESERIES_REGEX


def test_TIMESERIES():
    text = "0,-0.5\n59,-0.5\n60,-0.5\n61,-0.5\n9999,-0.5"
    assert TIMESERIES_REGEX.fullmatch(text)


def test_TIMESERIES_missing_separator():
    text = """0,-0.5\n9999,-0.50,-0.5"""
    assert not TIMESERIES_REGEX.fullmatch(text)
