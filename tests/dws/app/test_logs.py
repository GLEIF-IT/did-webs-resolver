import pytest

from dws import log_format_str, log_name


def test_truncated_formatter():
    """Test the TruncatedFormatter class."""
    import logging

    from dws.app.logs import TruncatedFormatter

    # Create an instance of TruncatedFormatter
    formatter = TruncatedFormatter(log_format_str)
    log_message = 'This is a test message.'
    formatted = formatter.format(
        logging.LogRecord(
            name='test_logger',
            level=logging.DEBUG,
            func='test_truncated_formatter',
            pathname='tests/dws/app/test_logs.py',
            lineno=42,
            msg=log_message,
            args=None,
            exc_info=None,
            sinfo=None,
        )
    )
    assert 'DEBUG' in formatted
    assert log_name in formatted
    assert 'test_logs' in formatted
    assert 'test_truncated' in formatted
    assert '42' in formatted
    assert log_message in formatted

    with pytest.raises(TypeError):
        formatter.format(
            logging.LogRecord(
                name='test_logger',
                level=logging.DEBUG,
                func='test_truncated_formatter',
                pathname='tests/dws/app/test_logs.py',
                lineno=42,
                msg='%s %s',
                args=('one',),  # invalid log message since expects two args and only one present
                exc_info=None,
                sinfo=None,
            )
        )


def test_truncated_formatter_preserves_shared_record():
    """Formatting for one handler must preserve fields used by later handlers."""
    import logging

    from dws.app.logs import TruncatedFormatter

    record = logging.LogRecord('test', logging.INFO, __file__, 42, 'hello', (), None, 'long_function_name')
    original = record.__dict__.copy()
    TruncatedFormatter(log_format_str).format(record)
    assert record.__dict__ == original
    assert logging.Formatter('%(lineno)d %(funcName)s').format(record) == '42 long_function_name'
