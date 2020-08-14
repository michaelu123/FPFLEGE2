import datetime
import os
import sys
import traceback
from decimal import Decimal

# Termine, bei denen Arbeitszeit und Sollzeit 0 sind
nichtArb = ["urlaub", "krank", "feiertag", "üst-abbau"]
# einige Termine, von denen wir annehmen, daß sie sich nicht am nächsten Tag wiederholen:
skipES = ["krank", "feiertag", "üst-abbau", "fortbildung", "supervision", "dienstbesprechung"]
wday2No = {"Mo": 0, "Di": 1, "Mi": 2, "Do": 3, "Fr": 4, "Sa": 5, "So": 6}
firstDay = None

# cannot get german weekdays on Android...
translate = {"Mo": "Mo", "Di": "Di", "Mi": "Mi", "Do": "Do", "Fr": "Fr", "Sa": "Sa", "So": "So",
             "Mon": "Mo", "Tue": "Di", "Wed": "Mi", "Thu": "Do", "Fri": "Fr", "Sat": "Sa", "Sun": "So",
             "Januar": "Januar", "Februar": "Februar", "März": "März", "April": "April",
             "Mai": "Mai", "Juni": "Juni", "Juli": "Juli", "August": "August",
             "September": "September", "Oktober": "Oktober", "November": "November", "Dezember": "Dezember",
             "January": "Januar", "February": "Februar", "March": "März",
             "May": "Mai", "June": "Juni", "July": "Juli",
             "October": "Oktober", "December": "Dezember"
             }


def stdBeg(_tag, _wtag2Stunden):
    return "08:00"


def stdEnd(tag, wtag2Stunden):
    stunden = wtag2Stunden[wday2No[day2WT(tag)]]
    if stunden == "04:00":
        return "12:00"
    if stunden == "06:00":
        return "14:00"
    if stunden == "06:30":
        return "15:00"
    if stunden == "07:00":
        return "15:30"
    if stunden == "08:00":
        return "16:30"
    return ""

def origin():
    if firstDay is not None:
        return firstDay;
    return datetime.date.today()

def num2Tag(d):
    if isinstance(d, str):
        d = int(d)
    return (origin() + datetime.timedelta(days=d)).strftime("%d.%m.%y")


def num2WT(d):
    if isinstance(d, str):
        d = int(d)
    wt = (origin() + datetime.timedelta(days=d)).strftime("%a")
    wt = translate[wt]
    return wt


def datum(d):
    return num2WT(d) + ", " + num2Tag(d)


def tag2Nummer(tag):  # tag = 01.01.20, today = 03.01.20 ->  tnr=-2
    for i in (range(5, -70, -1) if firstDay is None else range(0, 31, 1)):
        t = (origin() + datetime.timedelta(days=i)).strftime("%d.%m.%y")
        if t == tag:
            return i
    raise ValueError("Kann Tagesnummer für Tag " + tag + " nicht berechnen")


def day2WT(tag):  # d = 24.12.19
    day = datetime.date(2000 + int(tag[6:8]), int(tag[3:5]), int(tag[0:2]))
    wt = day.strftime("%a")
    wt = translate[wt]
    return wt


def monYYYY(mon):
    return translate[mon.strftime("%B")] + mon.strftime(" %Y")


def monYY(mon):
    return mon.strftime("%m.%y")


def t2m(t):
    sign = 1
    if t[0] == "-":
        sign = -1
        t = t[1:]
    col = t.find(':')
    m = int(t[0:col]) * 60 + int(t[col + 1:])
    return sign * m


def tadd(t1, t2):
    # 03:20 + 02:50 = 06:10
    m1 = t2m(t1)
    m2 = t2m(t2)
    m = m1 + m2
    sign = ""
    if m < 0:
        m = -m
        sign = "-"
    return sign + '{:02d}:{:02d}'.format(int(m / 60), int(m % 60))


def tsub(t1, t2):
    m1 = t2m(t1)
    m2 = t2m(t2)
    m = m1 - m2
    if m < 0:
        sign = "-"
        m = -m
    else:
        sign = ""
    res = sign + '{:02d}:{:02d}'.format(int(m / 60), int(m % 60))
    # print("tsub", t1, t2, res)
    return res


def tsubPause(t1, t2):
    # 06:10 - 03:20 = 02:50
    m3 = int(t1[3:5]) - int(t2[3:5])
    h3 = int(t1[0:2]) - int(t2[0:2])
    while m3 < 0:
        h3 -= 1
        m3 += 60
    if h3 > 6 or h3 == 6 and m3 > 0:  # h3:m3 > 06:00
        m3 -= 30
        while m3 < 0:
            h3 -= 1
            m3 += 60
    res = '{:02d}:{:02d}'.format(h3, m3)
    # print("tsubPause", t1, t2, res)
    return res

def hadd(sumh, row):
    es = row[2]
    t = tsubPause(row[4], row[3])
    try:
        sumh[es] = tadd(sumh[es], t)
    except:
        sumh[es] = t


def dadd(sumd, es):
    try:
        sumd[es] = sumd[es] + 1
    except:
        sumd[es] = 1


def hhmm2td(t):
    try:
        col = t.find(':')
        h = int(t[0:col])
        m = int(t[col+1:])
        # if t[0] == '-':
        #     return datetime.timedelta(0) - datetime.timedelta(hours=-h, minutes=m)
        # else:
        #     return datetime.timedelta(hours=int(t[0:col]), minutes=int(t[col+1:]))
        mdec = m / 60.0
        if h < 0:
            return float(h) - mdec
        else:
            return float(h) + mdec
    except Exception as e:
        print("cannot convert " + t + " to timedelta")
        raise e


def elimEmpty(tuples, x):
    return [t for t in tuples if t[x] != ""]


def printEx(msg, e):
    print(msg, e)
    traceback.print_exc(file=sys.stdout)


def getDataDir():
    if os.name == "posix":
        # Context.getExternalFilesDir()
        return "/storage/emulated/0/Android/data/org.fpflege.arbeitsblatt/files"
    return "."

def moneyfmt(value, places=2, curr='', sep=',', dp='.',
             pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    q = Decimal(10) ** -places      # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    if places:
        build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))

def char_range(c1, c2):
    """Generates the characters from `c1` to `c2`, inclusive."""
    for c in range(ord(c1), ord(c2)+1):
        yield chr(c)