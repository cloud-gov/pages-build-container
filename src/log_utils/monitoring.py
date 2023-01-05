from threading import Timer
import psutil
from humanize import naturalsize


# https://stackoverflow.com/a/48741004
class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def log_monitoring_metrics(logger):
    disk = psutil.disk_usage("/")
    logger.info(f'CPU Usage Percentage: {psutil.cpu_percent()}')
    logger.info(f'Memory Usage Percentage: {psutil.virtual_memory().percent}')
    logger.info(f'Disk usage: {naturalsize(disk.used)} / {naturalsize(disk.total)}')
