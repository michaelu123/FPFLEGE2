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
                            "mvv_euro": "", "kh": 0}
                    vals[x.name] = x.text
                    c.execute(
                        "INSERT INTO arbeitsblatt VALUES(:tag,:fnr,:einsatzstelle,:beginn,:ende,:fahrtzeit,:mvv_euro,:kh)",
                        vals)
        except Exception as e:
            utils.printEx("fam0:", e)

    def cbEvent(self, x):
        fnr = self.fnr
        tag = self.parent.parent.name
        tag = utils.num2Tag(tag)
        # print("cbEvent state", x.state, "active", x.active, "Famnr", fnr, "Tag", tag)
        try:
            with conn:
                c = conn.cursor()
                r1 = c.execute("UPDATE arbeitsblatt set kh = ? where tag=? and fnr=?", (int(x.active), tag, fnr))
                if r1.rowcount == 0:  # row did not yet exist
                    vals = {"tag": tag, "fnr": fnr, "einsatzstelle": "", "beginn": "", "ende": "", "fahrtzeit": "",
                            "mvv_euro": "", "kh": int(x.active)}
                    c.execute(
                        "INSERT INTO arbeitsblatt VALUES(:tag,:fnr,:einsatzstelle,:beginn,:ende,:fahrtzeit,:mvv_euro,:kh)",
                        vals)
        except Exception as e:
            utils.printEx("fam0:", e)

    def printFam(self):
        # print("fam", self)
        # print("famids", self.ids)
        fnr = self.fnr
        tag = self.parent.parent.name
        print("tag", tag, "fam" + str(fnr), "einss", self.ids.einsatzstelle.text, "beg", self.ids.beginn.text, "end",
              self.ids.ende.text, "kh", self.ids.kh.state)

    def vorschlag1(self, t):
        t = int(t)
        tag = utils.num2Tag(t)
        wt = utils.num2WT(t)
        if wt == "Sa" or wt == "So":
            return (tag, 1, "", "", "", "", "", 0)
        try:
            with conn:
                c = conn.cursor()
                for tv in range(t - 1, t - 5, -1):
                    wtv = utils.num2WT(tv)
                    if wtv == "Sa" or wtv == "So":
                        continue
                    tvtag = utils.num2Tag(tv)
                    c.execute("SELECT einsatzstelle, beginn, ende, fahrtzeit, mvv_euro, kh"
                              " from arbeitsblatt WHERE tag = ? and fnr = 1",
                              (tvtag,))
                    r = c.fetchmany(2)
                    r = utils.elimEmpty(r, 0)
                    if len(r) == 0:
                        break
                    elif len(r) == 1:
                        if r[0][0].lower() not in utils.skipES:
                            vals = r[0]
                            if self.app.menu.ids.wochenstunden.text == "38,5":  # übertrieben?
                                if wt == "Fr":
                                    vals = (vals[0], "08:00", "15:00", *vals[3:])
                                elif wtv == "Fr":
                                    vals = (vals[0], "08:00", "16:30", *vals[3:])
                            self.parent.vorschlagsTag = tvtag
                            return (tag, 1, *vals)
                    else:
                        raise ValueError("mehr als ein Eintrag für Tag {}, Fnr 1".format(tag))
        except Exception as e:
            utils.printEx("fam1:", e)
        tag = utils.num2Tag(t)
        return (tag, 1, "", "", "", "", "", 0)

    def vorschlag23(self, t, fnr):
        tag = utils.num2Tag(t)
        tvtag = self.parent.vorschlagsTag
        if tvtag is None:
            return (tag, fnr, "", "", "", "", "", 0)
        try:
            with conn:
                c = conn.cursor()
                c.execute("SELECT einsatzstelle, beginn, ende, fahrtzeit, mvv_euro, kh"
                          " from arbeitsblatt WHERE tag = ? and fnr = ?",
                          (tvtag, fnr))
                r = c.fetchmany(2)
                r = utils.elimEmpty(r, 0)
                if len(r) == 1:
                    vals = r[0]
                    return (tag, fnr, *vals)
                elif len(r) > 1:
                    raise ValueError("mehr als ein Eintrag für Tag {}, Fnr {}".format(tag, fnr))
        except Exception as e:
            utils.printEx("fam2:", e)
        return (tag, fnr, "", "", "", "", "", 0)

    def fillin(self, t, fnr, app):
        self.app = app
        tag = utils.num2Tag(t)
        if fnr == 1:
            self.parent.vorschlagsTag = None
        try:
            with conn:
                c = conn.cursor()
                c.execute("SELECT einsatzstelle, beginn, ende, fahrtzeit, mvv_euro, kh"
                          " from arbeitsblatt WHERE tag = ? and fnr = ?",
                          (tag, fnr))
                r = c.fetchmany(2)
                r = utils.elimEmpty(r, 0)
                if len(r) == 0:
                    if int(t) < 2:
                        vals = self.vorschlag1(t) if fnr == 1 else self.vorschlag23(t, fnr)
                        if vals[2] != "" or vals[3] != "" or vals[4] != "" or vals[5] != "" or vals[6] != "":
                            c.execute("INSERT INTO arbeitsblatt VALUES(?,?,?,?,?,?,?,?)", vals)
                    else:
                        vals = (tag, fnr, "", "", "", "", "", 0)
                elif len(r) == 1:
                    vals = (tag, fnr, *r[0])
                else:
                    raise ValueError("mehr als ein Eintrag für Tag {}, Fnr {}".format(tag, fnr))
                self.ids.einsatzstelle.text = vals[2]
                self.ids.beginn.text = vals[3]
                self.ids.ende.text = vals[4]
                self.ids.fahrtzeit.text = vals[5]
                self.ids.mvv_euro.text = vals[6]
                self.ids.kh.active = vals[7]
        except Exception as e:
            utils.printEx("fam3:", e)

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

    def clear(self):
        self.ids.einsatzstelle.text = ""
        self.ids.beginn.text = ""
        self.ids.ende.text = ""
        self.ids.fahrtzeit.text = ""
        self.ids.mvv_euro.text = ""
        self.ids.kh.active = 0

        tag = self.parent.parent.name
        tag = utils.num2Tag(tag)
        try:
            with conn:
                c = conn.cursor()
                r1 = c.execute("DELETE FROM arbeitsblatt where tag=?", (tag, ))
        except Exception as e:
            utils.printEx("fam0:", e)
