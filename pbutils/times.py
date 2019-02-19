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


if __name__ == '__main__':
    for x in [2, 67, 458, 3604, 3724, 86406, 86400+600+4, 86400+7200+600+4,
              31536000+20, 31536000+600+20, 31536000+10800+600+20, 31536000+43*86400+10800+600+20]:
        print(f'{x}, {duration(x)}')
