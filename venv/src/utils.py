import datetime

extras = {"urlaub", "feiertag", "krank"}
wday2No = {"Mo": 0, "Di": 1, "Mi": 2, "Do": 3, "Fr": 4, "Sa": 5, "So": 6}


def stdBeg(tag, wtag2Stunden):
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
    return (datetime.date.today() + datetime.timedelta(days=d)).strftime("%a")


def tag2Nummer(tag):  # tag = 01.01.20, today = 03.01.20 ->  tnr=-2
    for i in range(5, -70, -1):
        t = (datetime.date.today() + datetime.timedelta(days=i)).strftime("%d.%m.%y")
        if t == tag:
            return i
    raise ValueError("Kann Tagesnummer für Tag " + tag + " nicht berechnen")


def day2WT(tag):  # d = 24.12.19
    day = datetime.date(2000 + int(tag[6:8]), int(tag[3:5]), int(tag[0:2]))
    wday = day.strftime("%a")
    return wday


def tadd(t1, t2):
    # 03:20 + 02:50 = 06:10
    colt1 = t1.find(':')
    colt2 = t2.find(':')
    m3 = int(t1[colt1+1:]) + int(t2[colt2+1:])
    h3 = int(t1[0:colt1]) + int(t2[0:colt2])
    while m3 >= 60:
        h3 += 1
        m3 -= 60
    return '{:02d}:{:02d}'.format(h3, m3)


def tsub(t1, t2):
    # 06:10 - 03:20 = 02:50
    m3 = int(t1[3:5]) - int(t2[3:5])
    h3 = int(t1[0:2]) - int(t2[0:2])
    while m3 < 0:
        h3 -= 1
        m3 += 60
    if h3 >= 6:
        m3 -= 30
        while m3 < 0:
            h3 -= 1
            m3 += 60
    return '{:02d}:{:02d}'.format(h3, m3)


def radd(sums, row):
    es = row[2]
    t = tsub(row[4], row[3])
    try:
        sums[es] = tadd(sums[es], t)
    except:
        sums[es] = t
