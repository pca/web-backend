from django import template

register = template.Library()


@register.filter
def timeformat(time):
    time = int(time)

    if time == -1:
        return 'DNF'
    elif time == -2:
        return 'DNS'
    elif time > 0:
        ms = time % 100
        time -= ms
        seconds = int((time % 6000) / 100)
        minutes = int((time - (seconds * 100)) / 6000)
        # Add 0 prefix if ms is 1 digit
        if len(str(ms)) == 1:
            ms = '0{}'.format(ms)
        if minutes:
            # Add 0 prefix if seconds is 1 digit
            if len(str(seconds)) == 1:
                seconds = '0{}'.format(seconds)
            return '{}:{}.{}'.format(minutes, seconds, ms)
        return '{}.{}'.format(seconds, ms)

    return time
