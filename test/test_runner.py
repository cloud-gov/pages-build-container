import subprocess  # nosec
from unittest.mock import Mock, patch
from types import FunctionType

from runner import create_runner, run


@patch('runner.run')
@patch('runner.get_logger')
def test_create_runner_returns_runner_function(mock_get_logger, mock_run):
    name = 'step 1'
    logattrs = {}

    runner = create_runner(name, logattrs)

    assert(type(runner) is FunctionType)
    mock_get_logger.assert_called_once_with(name, logattrs)

    mock_logger = mock_get_logger.return_value
    command = 'command'
    runner(command)

    mock_run.assert_called_once_with(mock_logger, command, None, None)


@patch('subprocess.Popen', autospec=True)
def test_run(mock_popen):
    logger = Mock()
    command = 'foobar'

    run(logger, command)

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
