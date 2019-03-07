from time import localtime, asctime, gmtime, strftime, time, strptime, mktime


def duration(t):
    '''
    input: a number of seconds
    output: string of form '%s years, %s days, %s hours, %s mins, %s secs' % (years, days, hours, mins, secs)
    '''
    spm = 60
    mph = 60
    hpd = 24
    dpy = 365

    years, rem = divmod(t, dpy * hpd * mph * spm)
    days, rem = divmod(rem, hpd * mph * spm)
    hours, rem = divmod(rem, mph * spm)
    mins, secs = divmod(rem, spm)

    answer = ''
    if years:
        s = '' if years == 1 else 's'
        answer += '%s year%s, ' % (years, s)
    if days:
        s = '' if days == 1 else 's'
        answer += '%s day%s, ' % (days, s)
    if hours:
        s = '' if hours == 1 else 's'
        answer += '%s hour%s, ' % (hours, s)
    if mins:
        s = '' if mins == 1 else 's'
        answer += '%s min%s, ' % (mins, s)
    if secs:
        s = '' if secs == 1 else 's'
        answer += '%s sec%s' % (secs, s)
    return answer


def ep2asc(seconds=None, gmt=False, fmt=None):
    ''' Return a human readable version of seconds since the epoch. '''
    if seconds is None:
        seconds = time()
    f = gmtime if gmt else localtime
    if fmt:
        return strftime(fmt, f(seconds))
    else:
        return asctime(f(seconds))


def parse_std(timestr):
    ''' try to parse timestr according to common formats; return time.struct_time if ok, else None '''
    for fmt in __formats:
        try:
            return strptime(timestr, fmt)
        except ValueError:
            pass
    return None


__formats = [
    '%Y-%m-%d',
    '%Y/%m/%d',
    '%Y %m %d',

    '%y-%m-%d',
    '%y/%m/%d',
    '%y %m %d',

    '%m-%d-%Y',
    '%m/%d/%Y',
    '%m %d %Y',

    '%m-%d-%y',
    '%m/%d/%y',
    '%m %d %y',

    '%Y-%m-%d %H:%M:%S',
    '%Y/%m/%d %H:%M:%S',
    '%Y %m %d %H:%M:%S',

    '%y-%m-%d %H:%M:%S',
    '%y/%m/%d %H:%M:%S',
    '%y %m %d %H:%M:%S',

    '%m-%d-%Y %H:%M:%S',
    '%m/%d/%Y %H:%M:%S',
    '%m %d %Y %H:%M:%S',

    '%m-%d-%y %H:%M:%S',
    '%m/%d/%y %H:%M:%S',
    '%m %d %y %H:%M:%S',
]


if __name__ == '__main__':
    print('durations:')
    for x in [2, 67, 458, 3604, 3724, 86406, 86400+600+4, 86400+7200+600+4,
              31536000+20, 31536000+600+20, 31536000+10800+600+20, 31536000+43*86400+10800+600+20]:
        print(f'{x}, {duration(x)}')

    print('\nep2asc:')
    print(F"localtime: {ep2asc()}")
    print(F"gmttime:   {ep2asc(gmt=True)}\n")

    timestr = '2018-03-17 19:34:22'
    t = parse_std(timestr)
    print(f"parse_std:\n  input={timestr}\n  epoch={mktime(t)}\n  struct_time={t}")
