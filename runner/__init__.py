import subprocess  # nosec
from log_utils import get_logger


def run(logger, command, cwd=None, env=None):
    '''
    Run an OS command with provided cwd or env, stream logs to logger, and return the exit code.

    Errors that occur BEFORE the command is actually executed are caught and handled here.

    Errors encountered by the executed command are NOT caught. Instead a non-zero exit code
    will be returned to be handled by the caller.

    See https://docs.python.org/3/library/subprocess.html#popen-constructor for details.
    '''
    try:
        with subprocess.Popen(  # nosec
            command,
            cwd=cwd,
            env=env,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            bufsize=1,
            encoding='utf-8',
            text=True
        ) as p:
            logger.info(p.stdout.read())

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


def create_runner(name, logattrs):
    logger = get_logger(name, logattrs)

    def runner(command, cwd=None, env=None):
        return run(logger, command, cwd, env)

    return runner
