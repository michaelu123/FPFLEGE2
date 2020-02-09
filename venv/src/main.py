import locale
import sqlite3
from sqlite3 import OperationalError

import familie
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen, NoTransition, SlideTransition
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.textfield import MDTextField

Builder.load_string('''
#:import datetime datetime
#:import familie familie

<Page>:
    sm: sm
    BoxLayout:
        size: self.parent.size
        orientation: "vertical"
        MDToolbar:
            id: toolbar
            title: "Arbeitsbogen"
            md_bg_color: app.theme_cls.primary_color
            background_palette: 'Primary'
            elevation: 10
            left_action_items: [['menu', app.showMenu]]
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
                text: "Menu" if sm.current == "Menu" else \
                    (datetime.date.today() + datetime.timedelta(days=int(sm.current))).strftime("%a, %d.%m.%y")
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
            canvas.before:
                Color: 
                    rgba: (1,0,0,0)
                Rectangle:
                    size: self.size
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
    TextField:
        id: einsatzstelle
        name: "einsatzstelle"
        hint_text: str(fam.fnr) + ". Einsatzstelle/Pfl.-Nr./Urlaub/Krank/Fortbildung/Feiertag/Supervision/Sonstiges"
        helper_text: "Pfl.-Nr. oder Name"
        helper_text_mode: "on_focus"
        on_focus: if not self.focus: fam.famEvent(self)
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
            id: mvv_fahrt
            name: "mvv_fahrt"
            hint_text: "MVV-Fahrt"
            helper_text: "0,5 oder leer"
            helper_text_mode: "on_focus"
            padding: '12dp'
            on_focus: if not self.focus: fam.famEvent(self)
        TextField:
            id: mvv_euro
            name: "mvv_euro"
            hint_text: "MVV-Euro"
            helper_text: "Kosten Fahrkarte"
            helper_text_mode: "on_focus"
            padding: '12dp'
            on_focus: if not self.focus: fam.famEvent(self)
            
<Tag>:
    on_kv_post: self.init()
    BoxLayout:
        orientation: 'vertical'
        spacing: 20
        Familie:
            id: fam1
            fnr: 1
        Familie:
            id: fam2
            fnr: 2
        Familie:
            id: fam3
            fnr: 3
            
<Menu>:
    GridLayout:
        cols: 1
        spacing: 20
        padding: 30
        TextField:
            id: vorname
            hint_text: "Vorname"
        TextField:
            id: nachname
            hint_text: "Nachname"
        TextField:
            id: wochenstunden
            hint_text: "Wochenstunden"
        TextField:
            id: email_adresse
            hint_text: "Email-Adresse"
        MDRaisedButton:
            id: senden
            text: "Senden"
            on_release: 
                app.senden()
            
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
        self.ev = None
        # print("moveCB", self.t)
        if self.t < -100:
            app.nextScreen(1)
        elif self.t > 100:
            app.nextScreen(-1)


class Tag(Screen):

    def init(self):
        self.ids.fam1.fillin(self.name, 1)
        self.ids.fam2.fillin(self.name, 2)
        self.ids.fam3.fillin(self.name, 3)

    def printTag(self):
        for f in ["fam1", "fam2", "fam3"]:
            fam = self.ids[f]
            fam.printFam()


class Menu(Screen):
    pass


class TimeField(MDTextField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        if (col > 2):
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
                not "0" <= t[0] <= "9" or not "0" <= t[1] <= "9" or not "0" <= t[3] <= "9" or not "0" <= t[4] <= "9" or \
                 int(t[0:2]) > 23 or int(t[3:5]) > 59:
            t = ""
        self.text = t


class TextField(MDTextField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.write_tab = False

    gründe = ["Urlaub", "Krank", "Fortbildung", "Feiertag", "Supervision", "Sonstiges"]

    def normalize(self):
        t = self.text.strip()
        if self.hint_text.find("Einsatz") > 0:
            lc = t.lower()
            lcLen = len(lc)
            if lcLen >= 2:
                for grund in self.gründe:
                    if lcLen <= len(grund) and lc == grund[0:lcLen].lower():
                        self.text = grund
                        return
        elif self.hint_text.find("MVV-Fahrt") >= 0:
            if t != "" and t != "0,5":
                self.text = ""
                return
        elif self.hint_text.find("MVV-Euro") >= 0:
            pass

class TestApp(MDApp):
    tage = {}
    conn = ObjectProperty()

    def build(self):
        self.root = Page()
        self.root.sm.add_widget(Menu(name="Menu"))
        self.tage["0"] = self.root.sm.current_screen
        return self.root

    def showMenu(self, _):
        self.root.sm.transition = NoTransition()
        self.root.sm.current = "Menu"
        self.root.sm.transition = SlideTransition()

    def gotoScreen(self, t):
        sm = self.root.sm
        n = int(sm.current) + t
        if n > 5:
            n = 5
        if n < -40:
            n = -40
        n = str(n)
        if n not in self.tage:
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
            self.gotoScreen(t)
        elif t == 0:
            sm.transition.direction = 'right' if int(sm.current) > 0 else 'left'
            sm.current = "0"
        else:
            sm.transition.direction = 'left'
            self.gotoScreen(t)

    def senden(self):
        for t in self.tage:
            t = self.tage[t]
            t.printTag()

    def appEvent(self, x):
        print("appEvent", x)

def initDB():
    c = conn.cursor()
    try:
        with conn:
            c.execute("""CREATE TABLE arbeitsblatt(
            tag TEXT,
            fnr INTEGER,
            einsatzstelle TEXT,
            beginn TEXT,
            ende TEXT,
            mvv_fahrt TEXT,
            mvv_euro TEXT)
        """)
    except OperationalError:
        pass
    try:
        with conn:
            c.execute("""delete from arbeitsblatt where einsatzstelle="" and beginn="" and ende="" 
                and mvv_fahrt="" and mvv_euro="" """)
    except OperationalError:
        pass


if __name__ == '__main__':
    locale.setlocale(locale.LC_TIME, "German")
    conn = sqlite3.connect("test.db")
    familie.conn = conn
    app = TestApp()
    app.conn = conn
    initDB()
    app.run()
