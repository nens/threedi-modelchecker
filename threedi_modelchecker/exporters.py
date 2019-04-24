from collections import Counter


def print_errors(errors):
    """Simply prints all errors to stdout

    :param errors: iterator of BaseModelError
    """
    for error in errors:
        print(error)


def export_to_file(errors, file):
    """Write errors to a new file, separated with newlines.

    File cannot be an already existing file.

    :param errors: iterator of BaseModelError
    :param file:
    :return: None
    :raise FileExistsError: if the file already exists
    """
    with open(file, 'x') as f:
        for error in errors:
            f.write(str(error) + '\n')


def summarize_type_errors(errors):
    """Return an summary of the errors, aggregated on the type of errors

    Count for each type of error is returned.

    :param errors: iterator of BaseModelError
    :return: dict
    """
    def _get_error_type(errors):
        for error in errors:
            yield type(error).__name__
    summary = Counter(_get_error_type(errors))
    return summary, sum(summary.values())


def summarize_column_errors(errors):
    """Return a summary of the errors, aggregated on columns

    For each column the number of errors are returned. Columns with no errors
    are not returned.
    """
    def _get_error_table_column(errors):
        for error in errors:
            yield '%s.%s' % (error.column.table.name, error.column.name)
    summary = Counter(_get_error_table_column(errors))
    return summary, sum(summary.values())
