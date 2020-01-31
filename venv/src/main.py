import locale
import time

# from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivymd.textfields import MDTextField
from kivymd.app import MDApp

Builder.load_string('''
#:import datetime datetime
#:import MDLabel kivymd.label
#:import MDRaisedButton kivymd.button 
#:import MDTextField kivymd.textfields 

<Page>:
    sm: sm
    BoxLayout:
        size: self.parent.size
        orientation: "vertical"
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: 0.1
            MDRaisedButton:
                text: "Heute"
                size_hint: 1/8,1
                on_release: 
                    sm.transition.direction = 'right' if int(sm.current) > 0 else 'left'
                    sm.current = '0'
            MDRaisedButton:
                text: "<<"
                size_hint: 1/8,1
                on_release: 
                    sm.transition.direction = 'right'
                    sm.current = str(int(sm.current) - 7)
            MDRaisedButton:
                text: "<"
                size_hint: 1/8,1
                on_release: 
                    sm.transition.direction = 'right'
                    sm.current = str(int(sm.current) - 1)
            MDLabel:
                text: (datetime.date.today() + datetime.timedelta(days=int(sm.current))).strftime("%a, %d.%m.%y")
                size_hint: 3/8,1
                halign: 'center'
            MDRaisedButton:
                text: ">"
                size_hint: 1/8,1
                on_release: 
                    sm.transition.direction = 'left'
                    sm.current = str(int(sm.current) + 1)
            MDRaisedButton:
                text: ">>"
                size_hint: 1/8,1
                on_release: 
                    sm.transition.direction = 'left'
                    sm.current = str(int(sm.current) + 7)
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
    MDTextField:
        hint_text: str(fam.fnr) + ". Einsatzstelle"
        helper_text: "Pfl.-Nr. oder Name"
        helper_text_mode: "on_focus"
    BoxLayout:
        spacing: 30
        TimeField:
            hint_text: "Beginn"
            helper_text: "hh:mm"
            helper_text_mode: "on_focus"
            padding: '12dp'
        TimeField:
            hint_text: "Ende"
            helper_text: "hh:mm"
            helper_text_mode: "on_focus"
            padding: '12dp'
            
<Tag>:
    BoxLayout:
        orientation: 'vertical'
        spacing: 50
        Familie:
            fnr: 1
            size_hint_y: 0.5
        Familie:
            fnr: 2
            size_hint_y: 0.5
        BoxLayout:
            orientation: 'horizontal'
            MDTextField:
                hint_text: "MVV-Fahrt"
                helper_text: "0,5 oder leer"
                helper_text_mode: "on_focus"
                padding: '12dp'
            MDTextField:
                hint_text: "MVV-Euro"
                helper_text: "Kosten Fahrkarte"
                helper_text_mode: "on_focus"
                padding: '12dp'
        Familie:
            fnr: 3
            size_hint_y: 0.5
            
''')

class Page(Widget):
    sm = ObjectProperty(None)
    t = 0
    ev = None

    def on_touch_move(self, touch):
        print("touch", touch)
        self.t = touch.x - touch.ox
        if self.ev != None:
            self.ev.cancel()
        self.ev = Clock.schedule_interval(self.moveCB, 0.3)

    def moveCB(self, _):
        self.ev.cancel()
        self.ev = None
        print(self.t)
        if self.t < -100:
            self.sm.transition.direction = 'left'
            self.sm.current = str(int(self.sm.current) + 1)
        elif self.t > 100:
            self.sm.transition.direction = 'right'
            self.sm.current = str(int(self.sm.current) - 1)


class Tag(Screen):
    pass


class Familie(BoxLayout):
    fnr = NumericProperty()
    pass


class TimeField(MDTextField):
    pass


class TestApp(MDApp):

    def build(self):
        root = Page()
        for i in range(1, 70):
            root.sm.add_widget(Tag(name="-" + str(i)))
            root.sm.add_widget(Tag(name=str(i)))
        return root

    def addFamilie(self, s):
        s.add_widget(Familie(), 1)


if __name__ == '__main__':
    locale.setlocale(locale.LC_TIME, "German")
    TestApp().run()
