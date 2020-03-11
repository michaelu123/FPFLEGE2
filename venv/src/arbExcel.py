from decimal import Decimal

import openpyxl
import utils
from kivymd.uix.dialog import MDDialog
from openpyxl.utils.datetime import CALENDAR_MAC_1904

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
Sollstunden = 13
Ueberstunden = 14
Kumuliert = 15
Sentinel = 16


class ArbExcel:
    def __init__(self, month, dataDir, app):
        self.month = month
        self.dataDir = dataDir
        self.app = app
        self.tag = None
        self.kumArb = "00:00"
        self.kumSoll = "00:00"
        self.kumUeber = "00:00"
        pass

    def makeExcel(self):
        rows = self.checkComplete()
        if rows is None:
            return
        excelFile = self.writeExcel(rows)
        return excelFile

    def checkComplete(self):
        rows = []
        try:
            with conn:
                c = conn.cursor()
                c.execute("SELECT tag,fnr,einsatzstelle, beginn, ende, fahrtzeit, mvv_euro "
                          "from arbeitsblatt WHERE tag like ?",
                          ("__." + self.month,))
                while True:
                    r = c.fetchmany(100)
                    r = utils.elimEmpty(r, 2)
                    if len(r) == 0:
                        break
                    rows.extend(r)
        except Exception as e:
            utils.printEx("arbex0:", e)

        rows.sort(key=lambda xr: xr[0] + str(xr[1]))  # sort by tag and fnr, i.e. 01.01.20, 02.01.20,...,31.01.20
        lastTnr = 0
        nrows = []
        for row in rows:
            # print("row", row)
            if row[2] == "" and row[3] == "" and row[4] == "":
                continue
            self.tag = row[0]
            tnr = utils.tag2Nummer(self.tag)
            wday = utils.day2WT(self.tag)
            if wday == "Sa" or wday == "So":
                continue
            if wday == "Mo":
                lastTnr = tnr
            dayMiss = False
            if lastTnr != 0 and tnr > lastTnr + 1:
                self.tag = utils.num2Tag(lastTnr + 1)
                wday = utils.day2WT(self.tag)
                dayMiss = True
            lastTnr = tnr
            if dayMiss or (row[2] == "" or row[3] == "" or row[4] == ""):
                dia = MDDialog(size_hint=(.8, .4), title="Daten unvollständig",
                               text="Bitte Daten von " + wday + ", " + self.tag + " vervollständigen",
                               text_button_ok="OK", events_callback=self.evcb)
                dia.open()
                return None
            nrows.append(row)
        # print("Vollständig!")
        return nrows

    def evcb(self, _x, _y):
        tnr = utils.tag2Nummer(self.tag)
        self.app.gotoScreen(tnr, False)

    def makeRow(self, er, dsum, nsum, uesum, sollstunden):
        er[Arbeitsstunden] = utils.hhmm2td(dsum)
        ueberstunden = "00:00"
        if dsum == "00:00" and nsum == "00:00" and uesum == "00:00":
            # nicht möglich
            sollstunden = "00:00"
        elif dsum == "00:00" and nsum == "00:00" and uesum != "00:00":
            ueberstunden = "-" + sollstunden
        elif dsum == "00:00" and nsum != "00:00" and uesum == "00:00":
            sollstunden = "00:00"
        elif dsum == "00:00" and nsum != "00:00" and uesum != "00:00":
            ueberstunden = "-" + uesum
            sollstunden = utils.tsub(sollstunden, nsum)
        elif dsum != "00:00" and nsum == "00:00" and uesum == "00:00":
            ueberstunden = utils.tsub(dsum, sollstunden)
        elif dsum != "00:00" and nsum == "00:00" and uesum != "00:00":
            ueberstunden = utils.tsub(dsum, sollstunden)
        elif dsum != "00:00" and nsum != "00:00" and uesum == "00:00":
            sollstunden = utils.tsub(sollstunden, nsum)
        elif dsum != "00:00" and nsum != "00:00" and uesum != "00:00":
            sollstunden = utils.tsub(sollstunden, nsum)
            ueberstunden = utils.tsub(dsum, sollstunden)

        er[Ueberstunden] = utils.hhmm2td(ueberstunden)
        er[Sollstunden] = utils.hhmm2td(sollstunden)
        self.kumArb = utils.tadd(self.kumArb, dsum)
        self.kumSoll = utils.tadd(self.kumSoll, sollstunden)
        self.kumUeber = utils.tadd(self.kumUeber, ueberstunden)
        er[Kumuliert] = utils.hhmm2td(self.kumUeber)

    def writeExcel(self, rows):
        wb = openpyxl.Workbook()
        wb.epoch = CALENDAR_MAC_1904  # this enables negative timedeltas
        ws = wb.active
        ws.title = self.month
        ws.append(
            ["Tag", "1.Einsatzstelle", "Beginn", "Ende", "Fahrt", "MVV-Euro", "2.Einsatzstelle", "Beginn", "Ende1",
             "3.Einsatzstelle", "Beginn", "Ende", "Arbeitsstunden", "Sollstunden", "Überstunden", "Kumuliert"])
        ctag = ""
        er = None
        sumh = {}
        sumd = {"Fahrtzeit": 0}
        dsum = "00:00"
        nsum = "00:00"
        fsum = "00:00"
        uesum = "00:00"
        sollStunden = "00:00"
        mvvSumme = Decimal("0.00")
        rows.append(["99"])
        for row in rows:
            tag = row[0]
            if tag != ctag:
                if ctag != "":
                    self.makeRow(er, dsum, nsum, uesum, sollStunden)
                    ws.append(er)
                    mr = ws.max_row
                    for col in [Arbeitsstunden, Sollstunden, Ueberstunden, Kumuliert]:
                        ws.cell(row=mr, column=col+1).number_format = "[hh]:mm"
                    ws.cell(row=mr, column=6).number_format = "#,##0.00€"
                if tag == "99":
                    break
                er = ["" for _ in range(Sentinel)]
                wday = utils.day2WT(tag)
                sollStunden = self.app.menu.wtag2Stunden[utils.wday2No[wday]]
                er[Tag] = wday + ", " + tag
                ctag = tag
                dsum = "00:00"
                nsum = "00:00"
                uesum = "00:00"
            fnr = row[1]
            es = row[2]
            beginn = row[3]
            ende = row[4]
            if fnr == 1:
                er[Einsatzstelle1] = es
                er[Beginn1] = beginn
                er[Ende1] = ende
                if row[5] != "":
                    er[Fahrt] = float(row[5].replace(",", "."))
                if row[6] != "":
                    er[MVVEuro] = float(row[6].replace(",", "."))
                if row[5] != "":
                    fsum = utils.tadd(fsum, "00:30")
                    dsum = utils.tadd(dsum, "00:30")
                    utils.dadd(sumd, "Fahrtzeit")
            elif fnr == 2:
                er[Einsatzstelle2] = es
                er[Beginn2] = beginn
                er[Ende2] = ende
            elif fnr == 3:
                er[Einsatzstelle3] = es
                er[Beginn3] = beginn
                er[Ende3] = ende
            else:
                raise ValueError("Tag " + tag + " hat fnr " + fnr)
            utils.hadd(sumh, row)
            utils.dadd(sumd, es)
            dauer = utils.tsubPause(ende, beginn)
            if es.lower() == "üst-abbau":
                uesum = utils.tadd(uesum, dauer)
            elif es.lower() in utils.nichtArb:
                nsum = utils.tadd(nsum, dauer)
            else:
                dsum = utils.tadd(dsum, dauer)
            if row[6] != "":
                mvvSumme = mvvSumme + Decimal(row[6].replace(",", "."))

        mr = ws.max_row
        mrs = str(mr)
        ws.append([])
        ws.append(["Formeln:", "", "", "", "", "=SUM(F2:F"+mrs+")", "", "", "", "", "", "",
                   "=SUM(M2:M" + mrs + ")","=SUM(N2:N"+mrs+")", "=SUM(O2:O"+mrs+")"])
        mr = ws.max_row
        for col in [Arbeitsstunden, Sollstunden, Ueberstunden, Kumuliert]:
            ws.cell(row=mr, column=col + 1).number_format = "[hh]:mm"
        ws.cell(row=mr, column=6).number_format = "#,##0.00€"

        # mvvSumme = utils.moneyfmt(mvvSumme, sep='.', dp=',')
        mvvSumme = utils.moneyfmt(mvvSumme, sep='', dp='.')
        mvvSumme = float(mvvSumme)
        ws.append(["Summen:", "", "", "", "", mvvSumme, "", "", "", "", "", "",
                   utils.hhmm2td(self.kumArb), utils.hhmm2td(self.kumSoll), utils.hhmm2td(self.kumUeber)])
        mr = ws.max_row
        for col in [Arbeitsstunden, Sollstunden, Ueberstunden, Kumuliert]:
            ws.cell(row=mr, column=col + 1).number_format = "[hh]:mm"
        ws.cell(row=mr, column=6).number_format = "#,##0.00€"

        ws.append([])
        ws.append(["Einsatzstelle", "Tage", "Stunden"])
        sumh["Fahrtzeit"] = fsum
        tsum = "00:00"
        for es in sorted(sumh.keys()):
            if es == "Üst-Abbau":
                continue
            ws.append((es, sumd[es], utils.hhmm2td(sumh[es])))
            mr = ws.max_row
            ws.cell(row=mr, column=3).number_format = "[hh]:mm"
            if es.lower() not in utils.nichtArb:
                tsum = utils.tadd(tsum, sumh[es])
        ws.append([])
        ws.append(("Arbeitsstunden", utils.hhmm2td(tsum)))
        mr = ws.max_row
        ws.cell(row=mr, column=2).number_format = "[hh]:mm"
        ws.append(("Sollstunden", utils.hhmm2td(self.kumSoll)))
        mr = ws.max_row
        ws.cell(row=mr, column=2).number_format = "[hh]:mm"
        ws.append(("Überstunden", utils.hhmm2td(self.kumUeber)))
        mr = ws.max_row
        ws.cell(row=mr, column=2).number_format = "[hh]:mm"

        fn = self.dataDir + "/arbeitsblatt." + self.month + ".xlsx"
        wb.save(fn)
        return fn
