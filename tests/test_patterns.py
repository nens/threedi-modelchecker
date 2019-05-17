from threedi_modelchecker.checks.patterns import POSITIVE_FLOAT_LIST
from threedi_modelchecker.checks.patterns import TIMESERIES


def test_POSITIVE_FLOATS():
    text = '0'
    assert POSITIVE_FLOAT_LIST.fullmatch(text)



def test_POSITIVE_FLOATS_multiple():
    text = '0.0 0 1.1234567890 2'
    assert POSITIVE_FLOAT_LIST.fullmatch(text)


def test_POSITIVE_FLOATS_empty():
    text = ''
    assert not POSITIVE_FLOAT_LIST.fullmatch(text)


def test_POSITIVE_FLOATS_negative():
    text = '-5'
    assert not POSITIVE_FLOAT_LIST.fullmatch(text)


def test_POSITIVE_FLOATS_trailing_space():
    text = '0 '
    assert not POSITIVE_FLOAT_LIST.fullmatch(text)


def test_POSITIVE_FLOATS_invalid_char():
    text = '0 a'
    assert not POSITIVE_FLOAT_LIST.fullmatch(text)


def test_TIMESERIES():
    text = """0,-0.5
    59,-0.5
    60,-0.5
    61,-0.5
    9999,-0.5"""
    assert TIMESERIES.fullmatch(text)


def test_TIMESERIES_trailing_newline():
    text = """0,-0.5
    9999,-0.5\n"""
    assert not TIMESERIES.fullmatch(text)
