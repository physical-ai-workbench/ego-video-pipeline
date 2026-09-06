def format_time(seconds: float) -> str:
    """
    seconds -> MM:SS.mmm

    Examples
    --------
    1.0     -> 00:01.000
    12.35   -> 00:12.350
    63.5    -> 01:03.500
    """

    seconds = max(float(seconds), 0.0)

    minutes = int(seconds // 60)

    remaining_seconds = (
        seconds
        - minutes * 60
    )

    return (
        f"{minutes:02d}:"
        f"{remaining_seconds:06.3f}"
    )


def format_duration(seconds: float) -> str:
    return format_time(seconds)