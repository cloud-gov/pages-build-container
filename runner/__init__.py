import subprocess  # nosec
from log_utils import get_logger


def create_runner(name, logattrs):
    logger = get_logger(name, logattrs)

    def run(command, cwd=None, env=None):
        try:
            p = subprocess.Popen(  # nosec
                command,
                bufsize=1,
                cwd=cwd,
                encoding='utf-8',
                env=env,
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE,
                universal_newlines=True
            )
            while p.poll() is None:
                logger.info(p.stdout.readline())

            extra_output = p.communicate()[0]
            if extra_output:
                logger.info(extra_output)

            return p.returncode

        except OSError as err:
            logger.error('Encountered a problem executing `' + ' '.join(command) + '`.')
            logger.error(str(err))
            return 1

    return run
