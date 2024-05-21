import grp
import os
import pwd
import shlex
import subprocess  # nosec
from io import StringIO

NVM_PATH = '~/.nvm/nvm.sh'
RVM_PATH = '/usr/local/rvm/scripts/rvm'


def setuser():
    os.setgid(grp.getgrnam('rvm').gr_gid)
    os.setuid(pwd.getpwnam('customer').pw_uid)


def run(logger, command, cwd=None, env=None, shell=False, check=True, node=False, ruby=False, skip_log=False):  # noqa: E501
    '''
    Run an OS command with provided cwd or env, stream logs to logger, and return the exit code.

    Errors that occur BEFORE the command is actually executed are caught and handled here.

    Errors encountered by the executed command are caught unless `check=False`. In these cases a
    non-zero exit code will be returned to be handled by the caller.

    See https://docs.python.org/3/library/subprocess.html#popen-constructor for details.
    '''

    if ruby:
        command = f'source {RVM_PATH} && {command}'
        shell = True

    if node:
        command = f'source {NVM_PATH} && {command}'
        shell = True

    if isinstance(command, str) and not shell:
        command = shlex.split(command)

    # When a shell is needed, use `bash` instead of `sh`
    executable = '/bin/bash' if shell else None

    # aggregate stdout in case we need to return
    output = StringIO()

    try:
        p = subprocess.Popen(  # nosec
            command,
            cwd=cwd,
            env=env,
            shell=shell,
            executable=executable,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            bufsize=1,
            encoding='utf-8',
            text=True,
            preexec_fn=setuser
        )
        while p.poll() is None:
            line = p.stdout.readline().strip()
            if not skip_log:
                logger.info(line)
            output.write(line)

        line = p.stdout.readline().strip()
        if not skip_log:
            logger.info(line)
        output.write(line)

        if check:
            if p.returncode:
                raise subprocess.CalledProcessError(p.returncode, command)
            return output.getvalue()

        return p.returncode

    # This occurs when Popen itself is called with invalid arguments
    except ValueError as err:
        logger.error('Encountered a problem invoking Popen.')
        logger.error(str(err))

        if check:
            raise err

        return 1

    # This occurs when the command given to Popen cannot be executed.
    # Ex. the file doesn't exist, there was a typo, etc...
    except OSError as err:
        logger.error('Encountered a problem executing `' + ' '.join(command) + '`.')
        logger.error(str(err))

        if check:
            raise err

        return 1
