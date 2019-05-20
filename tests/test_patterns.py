from threedi_modelchecker.checks.patterns import POSITIVE_FLOAT_LIST_REGEX
from threedi_modelchecker.checks.patterns import TIMESERIES_REGEX


def test_POSITIVE_FLOATS():
    text = '0'
    assert POSITIVE_FLOAT_LIST_REGEX.fullmatch(text)



def test_POSITIVE_FLOATS_multiple():
    text = '0.0 0 1.1234567890 2'
    assert POSITIVE_FLOAT_LIST_REGEX.fullmatch(text)


def test_POSITIVE_FLOATS_empty():
    text = ''
    assert not POSITIVE_FLOAT_LIST_REGEX.fullmatch(text)


def test_POSITIVE_FLOATS_negative():
    text = '-5'
    assert not POSITIVE_FLOAT_LIST_REGEX.fullmatch(text)


def test_POSITIVE_FLOATS_trailing_space():
    text = '0 '
    assert not POSITIVE_FLOAT_LIST_REGEX.fullmatch(text)


def test_POSITIVE_FLOATS_invalid_char():
    text = '0 a'
    assert not POSITIVE_FLOAT_LIST_REGEX.fullmatch(text)


def test_TIMESERIES():
    text = "0,-0.5\n59,-0.5\n60,-0.5\n61,-0.5\n9999,-0.5"
    assert TIMESERIES_REGEX.fullmatch(text)


def test_TIMESERIES_trailing_newline():
    text = """0,-0.5\n9999,-0.5\n"""
    assert not TIMESERIES_REGEX.fullmatch(text)


def test_TIMESERIES_missing_separator():
    text = """0,-0.5\n9999,-0.50,-0.5"""
    assert not TIMESERIES_REGEX.fullmatch(text)
