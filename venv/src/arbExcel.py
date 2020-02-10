import datetime

from kivymd.uix.dialog import MDDialog

global conn

class ArbExcel:
    def __init__(self, month, app):
        self.month = month
        self.app = app
        self.tag = None
        pass

    def sende(self):
        self.checkComplete()
        pass

    def tag2Nummer(self, tag): # tag = 01.01.20, today = 03.01.20 ->  tnr=-2
        for i in range(5, -70, -1):
            t = (datetime.date.today() + datetime.timedelta(days=i)).strftime("%d.%m.%y")
            if t == tag:
                return i
        raise ValueError("kann Tagesnummer für Tag " + tag + " nicht berechnen")

    def checkComplete(self):
        rows = []
        try:
            with conn:
                c = conn.cursor()
                c.execute(
                    "SELECT tag,fnr,einsatzstelle, beginn, ende, mvv_fahrt, mvv_euro from arbeitsblatt WHERE tag like ?",
                    ("__." + self.month,))
                while True:
                    r = c.fetchmany(100)
                    if len(r) == 0:
                        break
                    rows.extend(r)
        except Exception as e:
            print("arbex2:", e)

        rows.sort(key=lambda row: row[0])  # sort by tag, i.e. 01.01.20, 02.01.20,...,31.01.20
        for row in rows:
            print("row", row)
            self.tag = row[0]
            day = datetime.date(2000 + int(self.tag[6:8]), int(self.tag[3:5]), int(self.tag[0:2]))
            wday = day.strftime("%a")
            if wday == "Sa" or wday == "So":
                continue
            if row[2] == "" or row[3] == "" or row[4] == "":
                dia = MDDialog(size_hint=(.8, .4), title="Daten unvollständig",
                               text="Bitte Daten von " + day.strftime("%a, %d.%m.%y") + " vervollständigen",
                               text_button_ok="OK", events_callback=self.evcb)
                dia.open()
                return
        print("Vollständig!")

    def evcb(self, x, y):
        tnr = self.tag2Nummer(self.tag)
        self.app.gotoScreen(tnr, False)
