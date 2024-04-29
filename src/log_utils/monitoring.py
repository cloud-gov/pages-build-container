from threading import Timer
import psutil

max_metrics = dict(
    cpu=0,
    mem=0,
    disk=0
)


# https://stackoverflow.com/a/48741004
class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def log_monitoring_metrics(logger, post_metrics):
    disk = psutil.disk_usage("/")

    # compute new maximum metrics and post to the application
    max_metrics["cpu"] = max(psutil.cpu_percent(), max_metrics["cpu"])
    max_metrics["mem"] = max(psutil.virtual_memory().percent, max_metrics["mem"])
    max_metrics["disk"] = max(disk.used, max_metrics["disk"])

    post_metrics(dict(machine=max_metrics))
