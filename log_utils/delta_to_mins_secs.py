def delta_to_mins_secs(delta):
    '''
    Converts a timedelta to a string of minutes and seconds.

    >>> td = timedelta(seconds=55)
    >>> delta_to_mins_secs(td)
    '55s'

    >>> td = timedelta(seconds=124)
    >>> delta_to_mins_secs(td)
    '2m 4s'
    '''
    secs = int(delta.total_seconds())
    if secs > 60:
        mins = int(secs // 60)
        secs = int(secs % 60)
        return f'{mins}m {secs}s'
    # else
    return f'{secs}s'
