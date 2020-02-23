import utils

from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout

global conn


class Familie(BoxLayout):
    fnr = NumericProperty()

    def famEvent(self, x):
        fnr = self.fnr
        tag = self.parent.parent.name
        tag = utils.num2Tag(tag)
        # print("famEvent", x.text, "Feld", x.name, "Famnr", fnr, "Tag", tag)
        x.normalize()
        try:
            with conn:
                c = conn.cursor()
                r1 = c.execute("UPDATE arbeitsblatt set " + x.name + " = ? where tag=? and fnr=?", (x.text, tag, fnr))
                if r1.rowcount == 0:  # row did not yet exist
                    vals = {"tag": tag, "fnr": fnr, "einsatzstelle": "", "beginn": "", "ende": "", "fahrtzeit": "",
                            "mvv_euro": ""}
                    vals[x.name] = x.text
                    c.execute(
                        "INSERT INTO arbeitsblatt VALUES(:tag,:fnr,:einsatzstelle,:beginn,:ende,:fahrtzeit,:mvv_euro)",
                        vals)
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
        t = int(t)
        tag = utils.num2Tag(t)
        wt = utils.num2WT(t)
        if wt == "Sa" or wt == "So":
            return (tag, 1, "", "", "", "", "")
        try:
            with conn:
                c = conn.cursor()
                for tv in range(t - 1, t - 5, -1):
                    wtv = utils.num2WT(tv)
                    if wtv == "Sa" or wtv == "So":
                        continue
                    tvtag = utils.num2Tag(tv)
                    c.execute("SELECT einsatzstelle, beginn, ende, fahrtzeit, mvv_euro"
                              " from arbeitsblatt WHERE tag = ? and fnr = 1",
                              (tvtag,))
                    r = c.fetchmany(2)
                    if len(r) == 0:
                        break
                    elif len(r) == 1:
                        if r[0][0].lower() not in utils.skipES:
                            vals = r[0]
                            if self.app.menu.ids.wochenstunden.text == "38,5": # übertrieben?
                                if wt == "Fr":
                                    vals = (vals[0], "08:00", "15:00", vals[3], vals[4])
                                elif wtv == "Fr":
                                    vals = (vals[0], "08:00", "16:30", vals[3], vals[4])
                            self.parent.vorschlagsTag = tvtag
                            return (tag, 1, *vals)
                    else:
                        raise ValueError("mehr als ein Eintrag für Tag {}, Fnr 1".format(tag))
        except Exception as e:
            print("ex2:", e)
        tag = utils.num2Tag(t)
        return (tag, 1, "", "", "", "", "")

    def vorschlag23(self, t, fnr):
        tag = utils.num2Tag(t)
        tvtag = self.parent.vorschlagsTag
        if tvtag is None:
            return (tag, fnr, "", "", "", "", "")
        try:
            with conn:
                c = conn.cursor()
                c.execute("SELECT einsatzstelle, beginn, ende, fahrtzeit, mvv_euro"
                          " from arbeitsblatt WHERE tag = ? and fnr = ?",
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

    def fillin(self, t, fnr, app):
        self.app = app
        tag = utils.num2Tag(t)
        if fnr == 1:
            self.parent.vorschlagsTag = None
        try:
            with conn:
                c = conn.cursor()
                c.execute("SELECT einsatzstelle, beginn, ende, fahrtzeit, mvv_euro"
                          " from arbeitsblatt WHERE tag = ? and fnr = ?",
                          (tag, fnr))
                r = c.fetchmany(2)
                if len(r) == 0:
                    if int(t) < 2:
                        vals = self.vorschlag1(t) if fnr == 1 else self.vorschlag23(t, fnr)
                        if vals[2] != "" or vals[3] != "" or vals[4] != "" or vals[5] != "" or vals[6] != "":
                            c.execute("INSERT INTO arbeitsblatt VALUES(?,?,?,?,?,?,?)", vals)
                    else:
                        vals = (tag, fnr, "", "", "", "", "")
                elif len(r) == 1:
                    vals = (tag, fnr, *r[0])
                else:
                    raise ValueError("mehr als ein Eintrag für Tag {}, Fnr {}".format(tag, fnr))
                self.ids.einsatzstelle.text = vals[2]
                self.ids.beginn.text = vals[3]
                self.ids.ende.text = vals[4]
                self.ids.fahrtzeit.text = vals[5]
                self.ids.mvv_euro.text = vals[6]
        except Exception as e:
            print("ex4:", e)

    def fillinStdBegEnd(self, wtag2Stunden):
        if self.ids.beginn.text != "" or self.ids.ende.text != "":
            return
        tag = self.parent.parent.name
        tag = utils.num2Tag(tag)
        self.ids.beginn.text = utils.stdBeg(tag, wtag2Stunden)
        self.famEvent(self.ids.beginn)
        self.ids.ende.text = utils.stdEnd(tag, wtag2Stunden)
        self.famEvent(self.ids.ende)
        pass
