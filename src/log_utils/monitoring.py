from threading import Timer
import psutil


# https://stackoverflow.com/a/48741004
class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def log_monitoring_metrics(logger):
    logger.info(f'CPU Percent: {psutil.cpu_percent()}')
    logger.info(f'Memory information: {dict(psutil.virtual_memory()._asdict())}')
    logger.info(f'Disk usage: {psutil.disk_usage("/")}')