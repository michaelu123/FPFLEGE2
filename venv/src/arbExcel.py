import openpyxl
import utils
from kivymd.uix.dialog import MDDialog

global conn

Tag = 0
Einsatzstelle1 = 1
Beginn1 = 2
Ende1 = 3
Fahrt = 4
MVVEuro = 5
Einsatzstelle2 = 6
Beginn2 = 7
Ende2 = 8
Einsatzstelle3 = 9
Beginn3 = 10
Ende3 = 11
Arbeitsstunden = 12
Ueberstunden = 13
Unterstunden = 14
Sentinel = 15

class ArbExcel:
    def __init__(self, month, app):
        self.month = month
        self.app = app
        self.tag = None
        pass

    def sende(self):
        rows = self.checkComplete()
        if rows is None:
            return
        self.writeExcel(rows)
        pass

    def checkComplete(self):
        rows = []
        try:
            with conn:
                c = conn.cursor()
                c.execute(
                    "SELECT tag,fnr,einsatzstelle, beginn, ende, fahrtzeit, mvv_euro from arbeitsblatt WHERE tag like ?",
                    ("__." + self.month,))
                while True:
                    r = c.fetchmany(100)
                    if len(r) == 0:
                        break
                    rows.extend(r)
        except Exception as e:
            print("arbex2:", e)

        rows.sort(key=lambda r: r[0] + str(r[1]))  # sort by tag and fnr, i.e. 01.01.20, 02.01.20,...,31.01.20
        for row in rows:
            # print("row", row)
            self.tag = row[0]
            wday = utils.day2WT(self.tag)
            if wday == "Sa" or wday == "So":
                continue
            if (row[2] != "" or row[3] != "" or row[4] != "") and (row[2] == "" or row[3] == "" or row[4] == ""):
                dia = MDDialog(size_hint=(.8, .4), title="Daten unvollständig",
                               text="Bitte Daten von " + wday + ", " + self.tag  + " vervollständigen",
                               text_button_ok="OK", events_callback=self.evcb)
                dia.open()
                return None
        # print("Vollständig!")
        return rows

    def evcb(self, x, y):
        tnr = utils.tag2Nummer(self.tag)
        self.app.gotoScreen(tnr, False)

    def writeExcel(self, rows):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = self.month
        wstunden = int(self.app.menu.ids.wochenstunden.text)
        ws.append(
            ["Tag", "1.Einsatzstelle", "Beginn", "Ende", "Fahrt", "MVV-Euro", "2.Einsatzstelle", "Beginn", "Ende1",
             "3.Einsatzstelle", "Beginn", "Ende", "Arbeitsstunden", "Überstunden"])
        ctag = ""
        er = None
        sums = {}
        dsum = "00:00"
        fsum = "00:00"
        for row in rows:
            tag = row[0]
            if tag != ctag:
                if ctag != "":
                    ws.append(er)
                er = ["" for x in range(Sentinel)]
                er[Tag] = tag
                ctag = tag
                dsum = "00:00"
            if row[1] == 1:
                er[Einsatzstelle1] = row[2]
                er[Beginn1] = row[3]
                er[Ende1] = row[4]
                er[Fahrt] = row[5]
                er[MVVEuro] = row[6]
                if row[5] != "":
                    fsum = utils.tadd(fsum, "00:30")
                    dsum = utils.tadd(dsum, "00:30")
            elif row[1] == 2:
                er[Einsatzstelle2] = row[2]
                er[Beginn2] = row[3]
                er[Ende2] = row[4]
            elif row[1] == 3:
                er[Einsatzstelle3] = row[2]
                er[Beginn3] = row[3]
                er[Ende3] = row[4]
            else:
                raise ValueError("Tag " + tag + " hat fnr " + row[1])
            utils.radd(sums, row)
            dsum = utils.tadd(dsum, utils.tsub(row[4], row[3]))
            er[Arbeitsstunden] = dsum

        ws.append([])
        ws.append([])
        tsum = "00:00"
        ws.append(["Einsatzstelle", "Stunden"])
        for es in sums.keys():
            ws.append((es, sums[es]))
            tsum = utils.tadd(tsum, sums[es])
        ws.append(("Fahrzeit", fsum))
        ws.append(("Summe", tsum))

        wb.save("arb.xlsx")
        pass
