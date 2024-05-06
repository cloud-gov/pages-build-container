from pytest import raises
import shlex
import subprocess  # nosec
from unittest.mock import Mock, patch

from runner import run, setuser, NVM_PATH, RVM_PATH


@patch('subprocess.Popen', autospec=True)
def test_run(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen.return_value = Mock(returncode=0, stdout=Mock(readline=Mock(return_value='foobar')))

    run(mock_logger, command)

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
        preexec_fn=setuser,
    )

    mock_logger.info.assert_called_once_with('foobar')


@patch('subprocess.Popen', autospec=True)
def test_run_popen_failure(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen.side_effect = ValueError('ugh')

    with raises(ValueError):
        run(mock_logger, command)

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
        preexec_fn=setuser,
    )

    mock_logger.error.assert_any_call('Encountered a problem invoking Popen.')
    mock_logger.error.assert_any_call('ugh')


@patch('subprocess.Popen', autospec=True)
def test_run_popen_failure_check_false(mock_popen):
    mock_logger = Mock()
    command = 'foobar'
    return_code = 1

    mock_popen.side_effect = ValueError('ugh')

    result = run(mock_logger, command, check=False)

    assert result == return_code

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
        preexec_fn=setuser,
    )

    mock_logger.error.assert_any_call('Encountered a problem invoking Popen.')
    mock_logger.error.assert_any_call('ugh')


@patch('subprocess.Popen', autospec=True)
def test_run_popen_output(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    string_output = 'string_output'
    mock_popen.return_value = Mock(returncode=0, stdout=Mock(readline=Mock(return_value=string_output)))  # noqa: E501

    result = run(mock_logger, command)
    assert result == string_output

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
        preexec_fn=setuser,
    )


@patch('subprocess.Popen', autospec=True)
def test_run_os_failure_check_false(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen.side_effect = OSError('ugh')

    result = run(mock_logger, command, check=False)

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
        preexec_fn=setuser
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
        run(mock_logger, command)

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
        preexec_fn=setuser
    )

    mock_logger.error.assert_any_call(
        'Encountered a problem executing `' + ' '.join(shlex.split(command)) + '`.'
    )
    mock_logger.error.assert_any_call('ugh')


@patch('subprocess.Popen', autospec=True)
def test_run_command_failure_check_false(mock_popen):
    mock_logger = Mock()
    command = 'foobar'
    return_code = 2

    mock_popen.return_value = Mock(returncode=return_code, stdout=Mock(readline=Mock(return_value='text')))  # noqa: E501

    result = run(mock_logger, command, check=False)

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
        preexec_fn=setuser
    )

    assert result == return_code


@patch('subprocess.Popen', autospec=True)
def test_run_command_failure_check_true(mock_popen):
    mock_logger = Mock()
    command = 'foobar'
    return_code = 2

    mock_popen.return_value = Mock(returncode=return_code, stdout=Mock(readline=Mock(return_value='text')))  # noqa: E501

    with raises(subprocess.CalledProcessError):
        run(mock_logger, command)

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
        preexec_fn=setuser
    )


@patch('subprocess.Popen', autospec=True)
def test_run_with_node(mock_popen):
    mock_logger = Mock()
    command = 'foobar'
    cwd = '/foo'
    env = {}

    mock_popen.return_value = Mock(returncode=0, stdout=Mock(readline=Mock(return_value='foobar')))

    run(mock_logger, command, cwd=cwd, env=env, node=True)

    mock_popen.assert_called_once_with(
        f'source {NVM_PATH} && {command}',
        cwd=cwd,
        env=env,
        shell=True,  # nosec
        executable='/bin/bash',
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        bufsize=1,
        encoding='utf-8',
        text=True,
        preexec_fn=setuser
    )


@patch('subprocess.Popen', autospec=True)
def test_run_with_ruby(mock_popen):
    mock_logger = Mock()
    command = 'foobar'
    cwd = '/foo'
    env = {}

    mock_popen.return_value = Mock(returncode=0, stdout=Mock(readline=Mock(return_value='foobar')))

    run(mock_logger, command, cwd=cwd, env=env, ruby=True)

    mock_popen.assert_called_once_with(
        f'source {RVM_PATH} && {command}',
        cwd=cwd,
        env=env,
        shell=True,  # nosec
        executable='/bin/bash',
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        bufsize=1,
        encoding='utf-8',
        text=True,
        preexec_fn=setuser
    )


def test_access_environ():
    mock_logger = Mock()
    command = 'cat /proc/1/environ'
    env = {}

    run(mock_logger, command, env=env, check=False)

    mock_logger.info.assert_any_call('cat: /proc/1/environ: Permission denied')


@patch('subprocess.Popen', autospec=True)
def test_run_skip_log(mock_popen):
    mock_logger = Mock()
    command = 'foobar'

    mock_popen.return_value = Mock(returncode=0, stdout=Mock(readline=Mock(return_value='foobar')))

    run(mock_logger, command, skip_log=True)

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
        preexec_fn=setuser,
    )

    mock_logger.info.assert_not_called()
