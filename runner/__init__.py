import shlex
import subprocess  # nosec

NVM_SH_PATH = '/usr/local/nvm/nvm.sh'


def run(logger, command, cwd=None, env=None, shell=False, check=False):
    '''
    Run an OS command with provided cwd or env, stream logs to logger, and return the exit code.

    Errors that occur BEFORE the command is actually executed are caught and handled here.

    Errors encountered by the executed command are NOT caught. Instead a non-zero exit code
    will be returned to be handled by the caller.

    See https://docs.python.org/3/library/subprocess.html#popen-constructor for details.
    '''

    if isinstance(command, str) and not shell:
        command = shlex.split(command)

    # When a shell is needed, use `bash` instead of `sh`
    executable = '/bin/bash' if shell else None

    try:
        with subprocess.Popen(  # nosec
            command,
            cwd=cwd,
            env=env,
            shell=shell,
            executable=executable,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            bufsize=1,
            encoding='utf-8',
            text=True
        ) as p:
            logger.info(p.stdout.read())

        if check and p.returncode:
            raise subprocess.CalledProcessError(p.returncode, command)

        return p.returncode

    # This occurs when Popen itself is called with invalid arguments
    except ValueError as err:
        logger.error('Encountered a problem invoking Popen.')
        logger.error(str(err))
        return 1

    # This occurs when the command given to Popen cannot be executed.
    # Ex. the file doesn't exist, there was a typo, etc...
    except OSError as err:
        logger.error('Encountered a problem executing `' + ' '.join(command) + '`.')
        logger.error(str(err))
        return 1


def run_with_node(logger, command, cwd=None, env=None, check=False):
    '''
    source nvm so node and npm are in the PATH

    TODO - refactor to put the appropriate node/npm binaries in PATH so this isn't necessary
    '''
    return run(
        logger,
        f'source {NVM_SH_PATH} && {command}',
        cwd=cwd,
        env=env,
        shell=True,  # nosec
        check=check,
    )
