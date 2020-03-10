import datetime

# Termine, bei denen die Arbeitszeit und SollZeit 0 ist
import os
import sys
import traceback

nichtArb = ["urlaub", "krank", "feiertag", "üst-abbau"]
# einige Termine, von denen wir annehmen, daß sie sich nicht am nächsten Tag wiederholen:
skipES = ["krank", "feiertag", "üst-abbau", "fortbildung", "supervision", "dienstbesprechung"]
wday2No = {"Mo": 0, "Di": 1, "Mi": 2, "Do": 3, "Fr": 4, "Sa": 5, "So": 6}

# cannot get german weekdays on Android...
translate = {"Mo": "Mo", "Di": "Di", "Mi": "Mi", "Do": "Do", "Fr": "Fr", "Sa": "Sa", "So": "So",
             "Mon": "Mo", "Tue": "Di", "Wed": "Mi", "Thu": "Do", "Fri": "Fr", "Sat": "Sa", "Sun": "So",
             "Januar": "Januar", "Februar": "Februar", "März": "März", "April": "April",
             "Mai": "Mai", "Juni": "Juni", "Juli": "Juli", "August": "August",
             "September": "September", "Oktober": "Oktober", "November": "November", "Dezember": "Dezember",
             "January": "Januar", "February": "Februar", "March": "März", "April": "April",
             "May": "Mai", "June": "Juni", "July": "Juli", "August": "August",
             "September": "September", "October": "Oktober", "November": "November", "December": "Dezember"
             }


def stdBeg(_tag, _wtag2Stunden):
    return "08:00"


def stdEnd(tag, wtag2Stunden):
    stunden = wtag2Stunden[wday2No[day2WT(tag)]]
    if stunden == "04:00":
        return "12:00"
    if stunden == "06:00":
        return "14:30"
    if stunden == "06:30":
        return "15:00"
    if stunden == "07:00":
        return "15:30"
    if stunden == "08:00":
        return "16:30"
    return ""


def num2Tag(d):
    if isinstance(d, str):
        d = int(d)
    return (datetime.date.today() + datetime.timedelta(days=d)).strftime("%d.%m.%y")


def num2WT(d):
    if isinstance(d, str):
        d = int(d)
    wt = (datetime.date.today() + datetime.timedelta(days=d)).strftime("%a")
    wt = translate[wt]
    return wt


def datum(d):
    return num2WT(d) + ", " + num2Tag(d)


def tag2Nummer(tag):  # tag = 01.01.20, today = 03.01.20 ->  tnr=-2
    for i in range(5, -70, -1):
        t = (datetime.date.today() + datetime.timedelta(days=i)).strftime("%d.%m.%y")
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
    return sign + '{:02d}:{:02d}'.format(int(m / 60), int(m % 60))


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
    return '{:02d}:{:02d}'.format(h3, m3)


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