import datetime
from sqlite3 import OperationalError

from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout

global conn
extras = {"urlaub", "fortbildung", "krank"}

def num2Tag(d):
    if isinstance(d, str): d = int(d)
    return (datetime.date.today() + datetime.timedelta(days=d)).strftime("%d.%m.%y")


def num2WT(d):
    if isinstance(d, str): d = int(d)
    return (datetime.date.today() + datetime.timedelta(days=d)).strftime("%a")


class Familie(BoxLayout):
    fnr = NumericProperty()

    def famEvent(self, x):
        fnr = self.fnr
        tag = self.parent.parent.name
        tag = num2Tag((tag))
        print("famEvent", x.text, "Feld", x.name, "Famnr", fnr, "Tag", tag)
        try:
            with conn:
                c = conn.cursor()
                c.execute("UPDATE arbeitsblatt set " + x.name + " = ? where tag=? and fnr=?", (x.text, tag, fnr))
        except Exception as e:
            print("ex1:", e)

    def printFam(self):
        # print("fam", self)
        # print("famids", self.ids)
        fnr = self.fnr
        tag = self.parent.parent.name
        print("tag", tag, "fam" + str(fnr), "einss", self.ids.einsatzstelle.text, "beg", self.ids.beginn.text, "end",
              self.ids.ende.text)

    def vorschlag1(self, t):
        self.parent.vorschlagsTag = None
        t = int(t)
        tag = num2Tag(t)
        wt = num2WT(t)
        if wt == "Sa" or wt == "So":
            return (tag, 1, "", "", "", "", "")
        try:
            with conn:
                c = conn.cursor()
                vals = None
                for tv in range(t - 1, t - 5, -1):
                    wt = num2WT(tv)
                    if wt == "Sa" or wt == "So":
                        continue
                    tvtag = num2Tag(tv)
                    c.execute(
                        "SELECT einsatzstelle, beginn, ende, mvv_fahrt, mvv_euro from arbeitsblatt WHERE tag = ? and fnr = 1",
                        (tvtag,))
                    r = c.fetchmany(2)
                    if len(r) == 0:
                        break
                    elif len(r) == 1:
                        if r[0][0].lower() not in extras:
                            vals = r[0]
                            self.parent.vorschlagsTag = tvtag
                            return (tag, 1, *vals)
                    else:
                        raise ValueError("mehr als ein Eintrag für Tag {}, Fnr 1".format(tag))
        except Exception as e:
            print("ex2:", e)
        tag = num2Tag(t)
        wt = num2WT(tv)
        return (tag, 1, "", "", "", "", "")

    def vorschlag23(self, t, fnr):
        tag = num2Tag(t)
        tvtag = self.parent.vorschlagsTag
        if tvtag is None:
            return (tag, fnr, "", "", "", "", "")
        try:
            with conn:
                c = conn.cursor()
                c.execute(
                    "SELECT einsatzstelle, beginn, ende, mvv_fahrt, mvv_euro from arbeitsblatt WHERE tag = ? and fnr = ?",
                    (tvtag, fnr))
                r = c.fetchmany(2)
                if len(r) == 1:
                    vals = r[0]
                    return (tag, fnr, *vals)
                elif len(r) > 1:
                    raise ValueError("mehr als ein Eintrag für Tag {}, Fnr {}".format(tag, fnr))
        except Exception as e:
            print("ex3:", e)
        return (tag, fnr, "", "", "", "", "")

    def fillin(self, t, fnr):
        tag = num2Tag(t)
        try:
            with conn:
                c = conn.cursor()
                c.execute(
                    "SELECT einsatzstelle, beginn, ende, mvv_fahrt, mvv_euro from arbeitsblatt WHERE tag = ? and fnr = ?",
                    (tag, fnr))
                r = c.fetchmany(2)
                if len(r) == 0:
                    vals = self.vorschlag1(t) if fnr == 1 else self.vorschlag23(t, fnr)
                    c.execute("INSERT INTO arbeitsblatt VALUES(?,?,?,?,?,?,?)", vals)
                elif len(r) == 1:
                    vals = (tag, fnr, *r[0])
                else:
                    raise ValueError("mehr als ein Eintrag für Tag {}, Fnr {}".format(tag, fnr))
                print("vals", vals)
                self.ids.einsatzstelle.text = vals[2]
                self.ids.beginn.text = vals[3]
                self.ids.ende.text = vals[4]
                self.ids.mvv_fahrt.text = vals[5]
                self.ids.mvv_euro.text = vals[6]
        except Exception as e:
            print("ex4:", e)
