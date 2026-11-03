WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


def window_hours(window):
    start = int(window["open"])
    end = int(window["close"])
    if start < end:
        return set(range(start, end))
    return set(range(start, 24)) | set(range(end))


def open_hours(operating_hours):
    hours = set()
    for day in WEEKDAYS:
        window = operating_hours.get(day)
        if window:
            hours |= window_hours(window)
    return hours


def is_open_on(operating_hours, weekday_index):
    return bool(operating_hours.get(WEEKDAYS[weekday_index]))


def night_hours(night_start, night_end):
    if night_start == night_end:
        return set()
    return window_hours({"open": night_start, "close": night_end})
