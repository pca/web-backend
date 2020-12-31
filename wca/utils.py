from datetime import timedelta


def parse_time(value):
    data = []
    time = timedelta(seconds=value)
    total_seconds = time.seconds
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        data.append(f"{hours:d}h")
    if minutes:
        data.append(f"{minutes:d}m")
    if seconds:
        if time.microseconds:
            data.append(f"{seconds:d}.{int(time.microseconds/10000)}s")
        else:
            data.append(f"{seconds:d}s")
    elif time.microseconds:
        data.append(f"0.{int(time.microseconds/10000)}s")

    return " ".join(data)


def parse_value(value, format):
    if value == -1:
        return "DNF"
    if value == -2:
        return "DNS"
    if value == 0:
        return None

    if format == "time":
        return parse_time(value / 100)
    if format == "number":
        return f"{value} moves"
    if format == "multi":
        value = str(value)

        # New format
        if len(value) == 9:
            difference = 99 - int(value[0:2])
            seconds = int(value[2:7]) if value[2:7] != "99999" else None
            missed = int(value[7:])
            solved = difference + missed
            total = solved + missed

            if seconds:
                time = parse_time(seconds / 1)

            return f"{time}; {solved} solved, {missed} missed, {total} total"

        # Old format
        if len(value) == 10 and value[0] == "1":
            solved = 99 - int(value[1:3])
            total = int(value[3:5])
            seconds = int(value[2:7]) if value[2:7] != "99999" else None

            if seconds:
                time = parse_time(seconds / 100)

            return f"{time}; {solved} solved, {total} total"
