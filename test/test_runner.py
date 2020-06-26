from pytest import raises
import shlex
import subprocess  # nosec
from unittest.mock import Mock, patch

from runner import run, run_with_node, NVM_SH_PATH


@patch('subprocess.Popen', autospec=True)
def test_run(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen_context = Mock(returncode=0, stdout=Mock(read=Mock(return_value='foobar')))
    mock_popen.return_value.__enter__.return_value = mock_popen_context

    result = run(mock_logger, command)

    mock_popen.assert_called_once_with(
        shlex.split(command),
        cwd=None,
        env=None,
        shell=False,
        executable=None,
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
        shlex.split(command),
        cwd=None,
        env=None,
        shell=False,
        executable=None,
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
def test_run_popen_failure_check_true(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen.side_effect = ValueError('ugh')

    with raises(ValueError, match='ugh'):
        run(mock_logger, command, check=True)

    mock_popen.assert_called_once_with(
        shlex.split(command),
        cwd=None,
        env=None,
        shell=False,
        executable=None,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        bufsize=1,
        encoding='utf-8',
        text=True,
    )

    mock_logger.error.assert_any_call('Encountered a problem invoking Popen.')
    mock_logger.error.assert_any_call('ugh')


@patch('subprocess.Popen', autospec=True)
def test_run_os_failure(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen.side_effect = OSError('ugh')

    result = run(mock_logger, command)

    mock_popen.assert_called_once_with(
        shlex.split(command),
        cwd=None,
        env=None,
        shell=False,
        executable=None,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        bufsize=1,
        encoding='utf-8',
        text=True
    )

    mock_logger.error.assert_any_call(
        'Encountered a problem executing `' + ' '.join(shlex.split(command)) + '`.'
    )
    mock_logger.error.assert_any_call('ugh')

    assert result == 1


@patch('subprocess.Popen', autospec=True)
def test_run_os_failure_check_true(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen.side_effect = OSError('ugh')

    with raises(OSError, match='ugh'):
        run(mock_logger, command, check=True)

    mock_popen.assert_called_once_with(
        shlex.split(command),
        cwd=None,
        env=None,
        shell=False,
        executable=None,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        bufsize=1,
        encoding='utf-8',
        text=True
    )

    mock_logger.error.assert_any_call(
        'Encountered a problem executing `' + ' '.join(shlex.split(command)) + '`.'
    )
    mock_logger.error.assert_any_call('ugh')


@patch('subprocess.Popen', autospec=True)
def test_run_command_failure(mock_popen):
    mock_logger = Mock()
    command = 'foobar'
    return_code = 2

    mock_popen.return_value.__enter__.return_value.returncode = return_code

    result = run(mock_logger, command)

    mock_popen.assert_called_once_with(
        shlex.split(command),
        cwd=None,
        env=None,
        shell=False,
        executable=None,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        bufsize=1,
        encoding='utf-8',
        text=True
    )

    assert result == return_code


@patch('subprocess.Popen', autospec=True)
def test_run_command_failure_check_true(mock_popen):
    mock_logger = Mock()
    command = 'foobar'
    return_code = 2

    mock_popen.return_value.__enter__.return_value.returncode = return_code

    with raises(subprocess.CalledProcessError):
        run(mock_logger, command, check=True)

    mock_popen.assert_called_once_with(
        shlex.split(command),
        cwd=None,
        env=None,
        shell=False,
        executable=None,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        bufsize=1,
        encoding='utf-8',
        text=True
    )


@patch('runner.run', autospec=True)
def test_run_with_node(mock_run):
    mock_logger = Mock()
    command = 'foobar'
    cwd = '/foo'
    env = {}
    check = True

    result = run_with_node(mock_logger, command, cwd=cwd, env=env, check=check)

    assert result == mock_run.return_value

    mock_run.assert_called_once_with(
        mock_logger,
        f'source {NVM_SH_PATH} && {command}',
        cwd=cwd,
        env=env,
        shell=True,  # nosec
        check=check,
    )
