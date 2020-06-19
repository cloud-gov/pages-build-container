import subprocess  # nosec
from unittest.mock import Mock, patch

from runner import run


@patch('subprocess.Popen', autospec=True)
def test_run(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen_context = Mock(returncode=0, stdout=Mock(read=Mock(return_value='foobar')))
    mock_popen.return_value.__enter__.return_value = mock_popen_context

    result = run(mock_logger, command)

    mock_popen.assert_called_once_with(
        command,
        cwd=None,
        env=None,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        bufsize=1,
        encoding='utf-8',
        text=True
    )

    mock_logger.info.assert_called_once_with('foobar')

    assert result == 0


@patch('subprocess.Popen', autospec=True)
def test_run_popen_failure(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen.side_effect = ValueError('ugh')

    result = run(mock_logger, command)

    mock_popen.assert_called_once_with(
        command,
        cwd=None,
        env=None,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        bufsize=1,
        encoding='utf-8',
        text=True
    )

    mock_logger.error.assert_any_call('Encountered a problem invoking Popen.')
    mock_logger.error.assert_any_call('ugh')

    assert result == 1


@patch('subprocess.Popen', autospec=True)
def test_run_command_failure(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen.side_effect = OSError('ugh')

    result = run(mock_logger, command)

    mock_popen.assert_called_once_with(
        command,
        cwd=None,
        env=None,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        bufsize=1,
        encoding='utf-8',
        text=True
    )

    mock_logger.error.assert_any_call(
        'Encountered a problem executing `' + ' '.join(command) + '`.'
    )
    mock_logger.error.assert_any_call('ugh')

    assert result == 1
