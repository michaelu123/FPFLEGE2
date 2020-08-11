import datetime
import locale
import os
import sqlite3
import time
from decimal import Decimal, getcontext
from sqlite3 import OperationalError

import arbExcel
import familie
import utils
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen, NoTransition, SlideTransition
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
# from plyer import storagepath
from plyer import filechooser

global conn

decCtx = getcontext()
decCtx.prec = 7  # 5.2 digits, max=99999.99

Builder.load_string('''
#:import os os
#:import datetime datetime
#:import familie familie
#:import utils utils
<Page>:
    sm: sm
    BoxLayout:
        size: self.parent.size
        orientation: "vertical"
        MDToolbar:
            id: toolbar
            title: "Arbeitsblatt"
            md_bg_color: app.theme_cls.primary_color
            background_palette: 'Primary'
            elevation: 10
            left_action_items: [['account', app.showMenu]]
            right_action_items: [['email', app.senden], ['delete', app.clear]] if not app.dokorrektur else [["file-excel", app.korrektur], ['email', app.senden], ['delete', app.clear]]
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: 0.1
            MDRaisedButton:
                text: "Heute"
                size_hint: 1/8,1
                on_release: 
                    app.nextScreen(0)
            MDRaisedButton:
                text: "<<"
                size_hint: 1/8,1
                on_release: 
                    app.nextScreen(-7)
            MDRaisedButton:
                text: "<"
                size_hint: 1/8,1
                on_release: 
                    app.nextScreen(-1)
            MDLabel:
                text: "Eigenschaften" if sm.current == "Menu" else utils.datum(sm.current)
                size_hint: 3/8,1
                halign: 'center'
            MDRaisedButton:
                text: ">"
                size_hint: 1/8,1
                on_release: 
                    app.nextScreen(1)
            MDRaisedButton:
                text: ">>"
                size_hint: 1/8,1
                on_release: 
                    app.nextScreen(7)
        ScreenManager:
            pos: self.pos
            size_hint_y: 0.9
            id: sm
            Tag: 
                name: "0"

<Familie>:
    orientation: 'vertical'
    spacing: 1
    id: fam
    padding: '12dp'
    BoxLayout:
        TextField:
            id: einsatzstelle
            fam: fam
            name: "einsatzstelle"
            hint_text: str(fam.fnr) + ". Name/Ur/Kr/Fe/Üs/Fo/Su/Di/So"
            helper_text: "Pfl.-Nr. oder Name, Urlaub, Krank,..."
            helper_text_mode: "on_focus"
            on_focus: if not self.focus: fam.famEvent(self)
        MDLabel:
            text: "KH:"
            theme_text_color: 'Hint'
            size_hint: None, None
            halign: 'left'
            size: dp(20), dp(48)
            font_size: '10sp'
        MDCheckbox:
            id: kh
            halign: 'left'
            size_hint: None, None
            size: dp(40), dp(48)
            on_state: fam.checkBoxEvent(self)
    BoxLayout:
        spacing: 30
        TimeField:
            id: beginn
            name: "beginn"
            hint_text: "Beginn"
            helper_text: "hh:mm"
            helper_text_mode: "on_focus"
            padding: '12dp'
            on_focus: if not self.focus: fam.famEvent(self)
        TimeField:
            id: ende
            name: "ende"
            hint_text: "Ende"
            helper_text: "hh:mm"
            helper_text_mode: "on_focus"
            padding: '12dp'
            on_focus: if not self.focus: fam.famEvent(self)
        TextField:
            id: fahrtzeit
            name: "fahrtzeit"
            hint_text: "Fahrtzeit"
            helper_text: "0,5 oder leer"
            helper_text_mode: "on_focus"
            padding: '12dp'
            on_focus: if not self.focus: fam.famEvent(self)
            disabled: fam.fnr == 3
        TextField:
            id: mvv_euro
            name: "mvv_euro"
            hint_text: "MVV-Euro"
            helper_text: "Kosten Fahrkarte"
            helper_text_mode: "on_focus"
            padding: '12dp'
            on_focus: if not self.focus: fam.famEvent(self)
            disabled: fam.fnr == 2 or fam.fnr == 3
            
<Tag>:
    id: tag
    on_kv_post: self.init()
    ScrollView:
        BoxLayout:
            size_hint_y: None
            height: dp(600)
            orientation: 'vertical'
            spacing: 20
            Familie:
                id: fam1
                tag: tag
                fnr: 1
            Familie:
                id: fam2
                tag: tag
                fnr: 2
            Familie:
                id: fam3
                tag: tag
                fnr: 3
            MDLabel:
            
<Menu>:
    on_kv_post: self.init()
    id: menu
    GridLayout:
        cols: 1
        spacing: 20
        padding: 30
        TextField:
            id: vorname
            name: "vorname"
            hint_text: "Vorname"
            on_focus: if not self.focus: menu.menuEvent(self)
        TextField:
            id: nachname
            name: "nachname"
            hint_text: "Nachname"
            on_focus: if not self.focus: menu.menuEvent(self)
        TextField:
            id: wochenstunden
            name: "wochenstunden"
            hint_text: "Wochenstunden"
            helper_text: "20, 30, 35 oder 38,5"
            helper_text_mode: "on_focus"
            on_focus: if not self.focus: menu.menuEvent(self)
        TextField:
            id: emailadresse
            name: "emailadresse"
            hint_text: "Email-Adresse"
            on_focus: if not self.focus: menu.menuEvent(self)
''')


class Page(Widget):
    sm = ObjectProperty(None)
    t = 0
    ev = None

    def on_touch_move(self, touch):
        # print("touch", touch)
        self.t = touch.x - touch.ox
        if self.ev is not None:
            self.ev.cancel()
        self.ev = Clock.schedule_interval(self.moveCB, 0.3)

    def moveCB(self, _):
        self.ev.cancel()
        # self.ev = None
        # print("moveCB", self.t)
        if self.t < -600:
            app.nextScreen(1)
        elif self.t > 600:
            app.nextScreen(-1)


class Tag(Screen):
    def init(self):
        if self.ids.fam1.ids.einsatzstelle.text != "":
            return
        self.ids.fam1.fillin(self.name, 1, app)
        self.ids.fam2.fillin(self.name, 2, app)
        self.ids.fam3.fillin(self.name, 3, app)

    def printTag(self):
        for f in ["fam1", "fam2", "fam3"]:
            fam = self.ids[f]
            fam.printFam()


class Menu(Screen):
    def setWtagStunden(self, wochenstunden):
        if wochenstunden == "20":
            self.wtag2Stunden = ("04:00", "04:00", "04:00", "04:00", "04:00", "00:00", "00:00")
        elif wochenstunden == "30":
            self.wtag2Stunden = ("06:00", "06:00", "06:00", "06:00", "06:00", "00:00", "00:00")
        elif wochenstunden == "35":
            self.wtag2Stunden = ("07:00", "07:00", "07:00", "07:00", "07:00", "00:00", "00:00")
        elif wochenstunden == "38,5":
            self.wtag2Stunden = ("08:00", "08:00", "08:00", "08:00", "06:30", "00:00", "00:00")
        else:
            self.wtag2Stunden = ("", "", "", "", "", "", "")

    def init(self):
        try:
            with conn:
                c = conn.cursor()
                c.execute("SELECT vorname, nachname, wochenstunden, emailadresse from eigenschaften")
                r = c.fetchmany(2)
                r = utils.elimEmpty(r, 1)
                if len(r) == 0:
                    vals = ("", "", "", "")
                elif len(r) == 1:
                    vals = r[0]
                else:
                    raise ValueError("mehr als ein Eintrag für eigenschaften")
                self.ids.vorname.text = vals[0]
                self.ids.nachname.text = vals[1]
                wochenstunden = vals[2]
                self.setWtagStunden(wochenstunden)
                self.ids.wochenstunden.text = vals[2]
                self.ids.emailadresse.text = vals[3]
        except Exception as e:
            utils.printEx("main0:", e)

    def menuEvent(self, x):
        x.normalize()
        try:
            with conn:
                c = conn.cursor()
                r1 = c.execute("UPDATE eigenschaften set " + x.name + " = ?", (x.text,))
                if r1.rowcount == 0:  # row did not yet exist
                    vals = {"vorname": "", "nachname": "", "wochenstunden": "", "emailadresse": ""}
                    vals[x.name] = x.text
                    r2 = c.execute(
                        "INSERT INTO eigenschaften VALUES(:vorname,:nachname,:wochenstunden,:emailadresse)", vals)
        except Exception as e:
            utils.printEx("main1:", e)
        if x.name == "wochenstunden":
            self.setWtagStunden(x.text)


class TimeField(MDTextField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.write_tab = False

    def normalize(self):
        t = self.text.strip()
        col = t.find(':')
        if col == 0:
            t = "00" + t
            col = 2
        if col == 1:
            t = "0" + t
            col = 2
        if col > 2:
            t = t[0:2] + t[col:]
            col = 2
        if col == 2:
            if len(t[2:]) == 1:
                t = t + "00"
            elif len(t[2:]) == 2:
                t = t + "0"
            else:
                t = t[0:5]
        col = t.find(',')
        if col == 0:
            t = "00" + t
            col = 2
        if col == 1:
            t = "0" + t
            col = 2
        if col > 2:
            t = t[0:2] + t[col:]
            col = 2
        if col > 0:
            t = t[0:2] + ":30"

        if col == -1:
            if len(t) == 1:
                t = "0" + t + ":00"
            elif len(t) == 2:
                t = t + ":00"
        if len(t) != 5 or t[2] != ":" or \
                not "0" <= t[0] <= "9" or not "0" <= t[1] <= "9" or not "0" <= t[3] <= "9" or not "0" <= t[4] <= "9" \
                or int(t[0:2]) > 23 or int(t[3:5]) > 59:
            toast("Uhrzeit hh:mm")
            t = ""
        try:
            hh = int(t[0:2])
            mm = int(t[3:5])
            if hh > 23 or mm > 59:
                toast("00:00-23:59")
                t = ""
        except:
            toast("00:00-23:59")
            t = ""
        self.text = t


class TextField(MDTextField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.write_tab = False

    gründe = ["Urlaub", "Krank", "Feiertag", "Üst-Abbau", "Fortbildung", "Supervision", "Dienstbesprechung",
              "Sonstiges"]

    def normalize(self):
        t = self.text.strip()
        if self.name == "einsatzstelle":
            lc = t.lower()
            lcLen = len(lc)
            if lcLen >= 2:
                for grund in self.gründe:
                    if lcLen <= len(grund) and lc == grund[0:lcLen].lower():
                        self.text = grund
                        break
            if self.fam.fnr == 1:  # and t.lower() in utils.extras:
                self.fam.fillinStdBegEnd(app.menu.wtag2Stunden)
        elif self.name == "fahrtzeit":
            if t != "" and t != "0,5":
                toast("Fahrtzeit 0,5 oder nichts")
                self.text = ""
                return
        elif self.name == "mvv_euro":
            try:
                d = Decimal(t.replace(",", "."))
                if int(d.compare(Decimal("5"))) < 0 or int(d.compare(Decimal(15))) > 0:
                    toast("MVV Kosten von 5 bis 15 €")
                    self.text = ""
                else:
                    self.text = utils.moneyfmt(d, sep='.', dp=',')
            except:
                toast("MVV Kosten von 5 bis 15 €")
                self.text = ""
        elif self.name == "wochenstunden":
            if t != "20" and t != "30" and t != "35" and t != "38,5":
                toast("Wochenstunden: 20, 30, 35, 38,5)")
                t = ""
            self.text = t


class ArbeitsBlatt(MDApp):
    tage = {}
    dokorrektur = os.environ.get("KORREKTUR") is not None

    # conn = ObjectProperty()

    def build(self):
        if os.name == "posix":
            perms = ["android.permission.READ_EXTERNAL_STORAGE",
                     "android.permission.WRITE_EXTERNAL_STORAGE"]
            haveperms = acquire_permissions(perms)
        dataDir = utils.getDataDir()
        os.makedirs(dataDir, exist_ok=True)
        db = dataDir + "/arbeitsblatt.db"

        print("db path", db)
        xconn = sqlite3.connect(db)
        familie.conn = xconn
        arbExcel.conn = xconn
        app.conn = xconn
        global conn
        conn = xconn
        initDB(xconn)

        self.menu = Menu(name="Menu")
        self.root = Page()
        self.root.sm.add_widget(self.menu)
        self.tage["0"] = self.root.sm.current_screen
        self.path = "C:/"
        return self.root

    def showMenu(self, _):
        self.root.sm.transition = NoTransition()
        self.root.sm.current = "Menu"
        self.root.sm.transition = SlideTransition()

    def clear(self, _):
        cur = self.root.sm.current
        try:
            t = self.tage[cur]
        except:  # clicked delete on menu page
            return
        for fam in ["fam1", "fam2", "fam3"]:
            t.ids[fam].clear()
        pass

    def gotoScreen(self, t, rel):
        sm = self.root.sm
        if rel:
            n = int(sm.current) + t
            if n > 5:
                n = 5
            if n < -62:
                n = -62
        else:
            n = t
        n = str(n)
        if n in self.tage:
            self.tage[n].init()
        else:
            self.tage[n] = Tag(name=n)
            sm.add_widget(self.tage[n])
        sm.current = n

    def nextScreen(self, t):
        sm = self.root.sm
        if sm.current == "Menu":
            sm.transition = NoTransition()
            sm.current = "0"
            sm.transition = SlideTransition()
        elif t < 0:
            sm.transition.direction = 'right'
            self.gotoScreen(t, True)
        elif t == 0:
            sm.transition.direction = 'right' if int(sm.current) > 0 else 'left'
            sm.current = "0"
        else:
            sm.transition.direction = 'left'
            self.gotoScreen(t, True)

    def senden(self, _):
        if app.menu.ids.emailadresse.text == "" or app.menu.ids.vorname.text == "" or \
                app.menu.ids.nachname.text == "" or app.menu.ids.wochenstunden.text == "":
            dia = MDDialog(size_hint=(.8, .4), title="Eigenschaften", text="Bitte Eigenschaften vollständig ausfüllen",
                           text_button_ok="OK")
            dia.open()
            self.root.sm.current = "Menu"
            return

        self.mon = datetime.date.today()
        mon = self.mon.month
        d = 0
        while self.mon.month == mon:
            d += 1
            self.mon = datetime.date.today() - datetime.timedelta(days=d)
        mon = utils.monYYYY(self.mon)
        dia = MDDialog(size_hint=(.8, .4), title="Monatsauswahl", text="Arbeitsblatt senden vom " + mon + "?",
                       text_button_cancel="Nein", text_button_ok="Ja", events_callback=self.evcb)
        dia.open()

    def evcb(self, x, _y):
        # print("evcb", self, x, y)
        if x == "Nein":
            mon = datetime.date.today()
            if mon == self.mon:
                return
            self.mon = mon
            mon = utils.monYYYY(self.mon)
            dia = MDDialog(size_hint=(.8, .4), title="Monatsauswahl", text="Arbeitsblatt senden vom " + mon + "?",
                           text_button_cancel="Nein", text_button_ok="Ja", events_callback=self.evcb)
            dia.open()
        else:
            dataDir = utils.getDataDir()
            excel = arbExcel.ArbExcel(utils.monYY(self.mon), dataDir, self)
            excelFile = excel.makeExcel()
            if os.name == "posix":
                import android_email
                mail = android_email.AndroidEmail()
                mon = utils.monYYYY(self.mon)
                mail.send(recipient=app.menu.ids.emailadresse.text, subject="Arbeitsblatt vom " + mon,
                          text="Anbei das Arbeitsblatt von " + app.menu.ids.vorname.text + " " +
                               app.menu.ids.nachname.text + " vom " + mon + ".",
                          attachment=excelFile)

    def korrektur(self, *args):
        try:
            with conn:
                c = conn.cursor()
                c.execute("delete from arbeitsblatt")
        except OperationalError:
            pass

        cwd = os.getcwd()
        path = filechooser.open_file(title="Bitte ein Arbeitsblatt auswählen", path=self.path, multiple=False,
                                     filters=[["Excel", "*.xlsx"]], preview=False)
        if not path:
            return

        path = path[0]
        self.path = os.path.dirname(path)
        dataDir = utils.getDataDir()
        excel = arbExcel.ArbExcel(0, dataDir, self)
        excelFile = excel.readExcel(path)


def initDB(conn):
    c = conn.cursor()
    try:
        with conn:
            c.execute("""CREATE TABLE arbeitsblatt(
            tag TEXT,
            fnr INTEGER,
            einsatzstelle TEXT,
            beginn TEXT,
            ende TEXT,
            fahrtzeit TEXT,
            mvv_euro TEXT,
            kh INTEGER)
            """)
    except OperationalError:
        pass
    try:
        with conn:
            c.execute("""CREATE TABLE eigenschaften(
            vorname TEXT,
            nachname TEXT,
            wochenstunden TEXT,
            emailadresse TEXT)
            """)
    except OperationalError:
        pass
    try:
        with conn:
            c.execute("""delete from arbeitsblatt where einsatzstelle="" and beginn="" and ende="" """)
    except OperationalError:
        pass


def acquire_permissions(permissions, timeout=30):
    from plyer.platforms.android import activity

    def allgranted(permissions):
        for perm in permissions:
            r = activity.checkCurrentPermission(perm)
            if r == 0:
                return False
        return True

    haveperms = allgranted(permissions)
    if haveperms:
        # we have the permission and are ready
        return True

    # invoke the permissions dialog
    activity.requestPermissions(permissions)

    # now poll for the permission (UGLY but we cant use android Activity's onRequestPermissionsResult)
    t0 = time.time()
    while time.time() - t0 < timeout and not haveperms:
        # in the poll loop we could add a short sleep for performance issues?
        haveperms = allgranted(permissions)
        time.sleep(1)

    return haveperms


if __name__ == '__main__':
    try:
        # this seems to have no effect on android for strftime...
        locale.setlocale(locale.LC_ALL, "")
    except Exception as e:
        utils.printEx("setlocale", e)
    app = ArbeitsBlatt()
    app.run()

    """
    try:
        print("home", storagepath.get_home_dir())  # /data
    except:
        pass
    try:
        print("extstor", storagepath.get_external_storage_dir())  # /storage/emulated/0
    except:
        pass
    try:
        print("sdcard", storagepath.get_sdcard_dir())  # None
    except:
        pass
    try:
        print("root", storagepath.get_root_dir())  # /system
    except:
        pass
    try:
        print("docs", storagepath.get_documents_dir())  # /storage/emulated/0/Documents
    except:
        pass
    try:
        print("down", storagepath.get_downloads_dir())  # /storage/emulated/0/Download
    except:
        pass
    try:
        print("app", storagepath.get_application_dir())  # /data/user/0
    except:
        pass
    print("cwd", os.getcwd())  # /data/data/org.fpflege.arbeitsblatt/files/app
    print("env", os.environ)

    {    'PATH': '/sbin:/system/sbin:/system/bin:/system/xbin:/vendor/bin:/vendor/xbin',
         'DOWNLOAD_CACHE': '/data/cache', 
         'ANDROID_BOOTLOGO': '1', 
         'ANDROID_ROOT': '/system',
         'ANDROID_ASSETS': '/system/app', 
         'ANDROID_DATA': '/data', 
         'ANDROID_STORAGE': '/storage',
         'EXTERNAL_STORAGE': '/sdcard', 
         'ASEC_MOUNTPOINT': '/mnt/asec',
         'BOOTCLASSPATH': '/system/framework/core-oj.jar:/system/framework/core-libart.jar:/system/framework/conscrypt.jar:/system/framework/okhttp.jar:/system/framework/bouncycastle.jar:/system/framework/apache-xml.jar:/system/framework/legacy-test.jar:/system/framework/ext.jar:/system/framework/framework.jar:/system/framework/telephony-common.jar:/system/framework/voip-common.jar:/system/framework/ims-common.jar:/system/framework/org.apache.http.legacy.boot.jar:/system/framework/android.hidl.base-V1.0-java.jar:/system/framework/android.hidl.manager-V1.0-java.jar',
         'SYSTEMSERVERCLASSPATH': '/system/framework/services.jar:/system/framework/ethernet-service.jar:/system/framework/wifi-service.jar:/system/framework/com.android.location.provider.jar',
         'ANDROID_SOCKET_zygote_secondary': '9', 
         'ANDROID_ENTRYPOINT': 'main.pyc',
         'ANDROID_ARGUMENT': '/data/user/0/org.fpflege.arbeitsblatt/files/app',
         'ANDROID_APP_PATH': '/data/user/0/org.fpflege.arbeitsblatt/files/app',
         'ANDROID_PRIVATE': '/data/user/0/org.fpflege.arbeitsblatt/files',
         'ANDROID_UNPACK': '/data/user/0/org.fpflege.arbeitsblatt/files/app',
         'PYTHONHOME': '/data/user/0/org.fpflege.arbeitsblatt/files/app',
         'PYTHONPATH': '/data/user/0/org.fpflege.arbeitsblatt/files/app:/data/user/0/org.fpflege.arbeitsblatt/files/app/lib',
         'PYTHONOPTIMIZE': '2', 
         'P4A_BOOTSTRAP': 'SDL2', 
         'PYTHON_NAME': 'python', 
         'P4A_IS_WINDOWED': 'True',
         'P4A_ORIENTATION': 'portrait', 
         'P4A_NUMERIC_VERSION': 'None', 
         'P4A_MINSDK': '21', 
         'LC_CTYPE': 'C.UTF-8'
    }
    """
