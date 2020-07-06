from .exceptions import StepException


def wrap(fn, msg):
    def wrapped(*args, **kwargs):
        result = fn(*args, **kwargs)
        if result:
            raise StepException(msg)
        return result
    return wrapped
