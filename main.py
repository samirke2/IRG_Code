# -*- coding: utf-8 -*-
"""
مولّد رموز التفعيل (للمطوّر فقط) - Kivy
- ضعه في مستودع خاص منفصل، ولا تضعه أبداً في مستودع تطبيق الزبائن.
- SECRET يجب أن يطابق SECRET في تطبيق الحاسبة (main.py).
"""
import hashlib
import hmac
import os
from urllib.parse import quote

import arabic_reshaper

try:
    from bidi.algorithm import get_display
except Exception:
    try:
        from bidi import get_display
    except Exception:
        import re as _re
        _AR = '\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF'

        def get_display(text):
            parts = _re.findall('[%s]+|[^%s]+' % (_AR, _AR), text)
            return ''.join(p[::-1] if _re.match('[%s]' % _AR, p) else p
                           for p in parts[::-1])

from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Line, Mesh, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty
from kivy.resources import resource_find
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex as hexc
from kivy.utils import platform

SECRET = b'4f2b7273efe1abb61fe6f0e33c2d6f65'

# ---------------- الخط ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_font(name):
    p = os.path.join(BASE_DIR, name)
    return p if os.path.exists(p) else None


_regular = _find_font('Sahel.ttf') or resource_find('data/fonts/DejaVuSans.ttf')
_bold = _find_font('Sahel-Bold.ttf') or _regular
if _regular:
    LabelBase.register(name='custom_font', fn_regular=_regular, fn_bold=_bold)
    FONT = 'custom_font'
else:
    FONT = 'Roboto'


def ar(t):
    return get_display(arabic_reshaper.reshape(t))


# ---------------- الألوان ----------------
BG = hexc('#0E2623')
PANEL = hexc('#15403A')
PANEL_EDGE = hexc('#2A6358')
FIELD = hexc('#0B1D1B')
TEXT = hexc('#EAF4EF')
MUTED = hexc('#8FB3A8')
ACCENT = hexc('#F2A93B')
ACCENT_DARK = hexc('#C77F14')
INK = hexc('#10231F')
TAB_OFF = hexc('#1D554C')


def share_whatsapp(text, phone=''):
    url = 'https://wa.me/%s?text=%s' % (phone, quote(text))
    try:
        from jnius import autoclass
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        act = autoclass('org.kivy.android.PythonActivity').mActivity
        act.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
    except Exception:
        import webbrowser
        webbrowser.open(url)


def wa_phone(raw):
    """يحوّل رقماً جزائرياً (0555...) إلى صيغة دولية (213555...)."""
    d = ''.join(ch for ch in raw if ch.isdigit())
    if d.startswith('00'):
        d = d[2:]
    elif d.startswith('0'):
        d = '213' + d[1:]
    return d


def make_code(device_id):
    h = hmac.new(SECRET, device_id.upper().encode(), hashlib.sha256)
    h = h.hexdigest()[:12].upper()
    return '-'.join(h[i:i + 4] for i in range(0, 12, 4))


# ---------------- الرسم ----------------
def set_poly(mesh, pts):
    v = []
    for i in range(0, len(pts), 2):
        v += [pts[i], pts[i + 1], 0, 0]
    mesh.vertices = v
    mesh.indices = list(range(len(pts) // 2))


def chamfer_pts(x, y, w, h, c):
    c = max(0, min(c, w / 2.0, h / 2.0))
    return [x + c, y, x + w, y, x + w, y + h - c, x + w - c, y + h,
            x, y + h, x, y + c]


def para_pts(x, y, w, h, s):
    s = max(0, min(s, w / 3.0))
    return [x + s, y, x + w, y, x + w - s, y + h, x, y + h]


def gloss_pts(x, y, w, h, s):
    s = max(0, min(s, w / 3.0))
    return [x + s * 0.5, y + h * 0.5, x + w - s * 0.5, y + h * 0.5,
            x + w - s, y + h, x, y + h]


def L(text='', shape=True, halign='right', **kw):
    kw.setdefault('font_name', FONT)
    kw.setdefault('color', TEXT)
    kw.setdefault('font_size', sp(15))
    lbl = Label(text=ar(text) if (shape and text) else text,
                halign=halign, valign='middle', **kw)
    lbl.bind(size=lambda w, s: setattr(w, 'text_size', s))
    return lbl


class Panel(BoxLayout):
    def __init__(self, fill=PANEL, edge=PANEL_EDGE, cut=dp(14), **kw):
        kw.setdefault('orientation', 'vertical')
        super().__init__(**kw)
        self.cut = cut
        with self.canvas.before:
            Color(0, 0, 0, 0.32)
            self._sh = Mesh(mode='triangle_fan')
            Color(*fill)
            self._body = Mesh(mode='triangle_fan')
            self._ce = Color(*edge)
            self._ln = Line(points=[0, 0, 0, 0, 0, 0], width=1.2, close=True)
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def set_edge(self, rgba):
        self._ce.rgba = rgba

    def _draw(self, *a):
        x, y = self.pos
        w, h = self.size
        set_poly(self._sh, chamfer_pts(x, y - dp(3), w, h, self.cut))
        pts = chamfer_pts(x, y, w, h, self.cut)
        set_poly(self._body, pts)
        self._ln.points = pts


class SkewButton(ButtonBehavior, Label):
    bg = ListProperty(ACCENT)
    bg_down = ListProperty(ACCENT_DARK)
    fg = ListProperty(INK)
    skew = NumericProperty(dp(16))

    def __init__(self, **kw):
        if kw.get('text'):
            kw['text'] = ar(kw['text'])
        kw.setdefault('font_name', FONT)
        kw.setdefault('font_size', sp(17))
        kw.setdefault('bold', True)
        super().__init__(**kw)
        with self.canvas.before:
            Color(0, 0, 0, 0.38)
            self._sh = Mesh(mode='triangle_fan')
            self._cb = Color(*self.bg)
            self._body = Mesh(mode='triangle_fan')
            Color(1, 1, 1, 0.13)
            self._gl = Mesh(mode='triangle_fan')
        self.bind(pos=self._draw, size=self._draw, state=self._draw)
        self._draw()

    def _draw(self, *a):
        x, y = self.pos
        w, h = self.size
        down = self.state == 'down'
        d = dp(4)
        lift = 0 if down else d
        hh = h - d
        set_poly(self._sh, para_pts(x, y, w, hh, self.skew))
        set_poly(self._body, para_pts(x, y + lift, w, hh, self.skew))
        set_poly(self._gl, gloss_pts(x, y + lift, w, hh, self.skew))
        self._cb.rgba = self.bg_down if down else self.bg
        self.color = self.fg
        self.padding = (0, 0, 0, 0 if down else d)


# ---------------- الواجهة ----------------
class KeyGen(BoxLayout):

    def __init__(self, **kw):
        super().__init__(orientation='vertical',
                         padding=[dp(12), dp(10), dp(12), dp(10)],
                         spacing=dp(12), **kw)
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(self._bg, 'pos', v),
                  size=lambda w, v: setattr(self._bg, 'size', v))

        head = Panel(edge=ACCENT, cut=dp(18), size_hint_y=None,
                     height=dp(76), padding=[dp(16), dp(8)], spacing=dp(2))
        head.add_widget(L('مولّد رموز التفعيل', bold=True, color=ACCENT,
                          font_size=sp(24)))
        head.add_widget(L('للمطوّر فقط', color=MUTED, font_size=sp(13)))
        self.add_widget(head)

        self.add_widget(L('رقم جهاز الزبون', color=MUTED, font_size=sp(13),
                          size_hint_y=None, height=dp(20)))
        box = Panel(fill=FIELD, cut=dp(10), orientation='horizontal',
                    padding=[dp(12), 0], size_hint_y=None, height=dp(52))
        self.inp = TextInput(
            multiline=False, hint_text='ABCD1234EF567890', font_name=FONT,
            font_size=sp(19), halign='center', background_normal='',
            background_active='', background_color=(0, 0, 0, 0),
            foreground_color=TEXT, hint_text_color=(1, 1, 1, 0.25),
            cursor_color=ACCENT, write_tab=False)
        self.inp.bind(
            size=lambda w, *_: setattr(
                w, 'padding', [0, max(0, (w.height - w.line_height) / 2.0)] * 2),
            focus=lambda w, f: box.set_edge(ACCENT if f else PANEL_EDGE),
            text=self.update)
        box.add_widget(self.inp)
        self.add_widget(box)

        self.add_widget(L('رقم هاتف الزبون اختياري', color=MUTED,
                          font_size=sp(13), size_hint_y=None, height=dp(20)))
        pbox = Panel(fill=FIELD, cut=dp(10), orientation='horizontal',
                     padding=[dp(12), 0], size_hint_y=None, height=dp(52))
        self.phone = TextInput(
            multiline=False, input_filter='int', hint_text='0555 00 00 00',
            font_name=FONT, font_size=sp(19), halign='center',
            background_normal='', background_active='',
            background_color=(0, 0, 0, 0), foreground_color=TEXT,
            hint_text_color=(1, 1, 1, 0.25), cursor_color=ACCENT,
            write_tab=False)
        self.phone.bind(
            size=lambda w, *_: setattr(
                w, 'padding', [0, max(0, (w.height - w.line_height) / 2.0)] * 2),
            focus=lambda w, f: pbox.set_edge(ACCENT if f else PANEL_EDGE))
        pbox.add_widget(self.phone)
        self.add_widget(pbox)

        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10),
                        padding=[dp(6), 0])
        clear = SkewButton(text='مسح', bg=TAB_OFF, bg_down=PANEL_EDGE,
                           fg=TEXT, font_size=sp(15))
        paste = SkewButton(text='لصق', bg=TAB_OFF, bg_down=PANEL_EDGE,
                           fg=TEXT, font_size=sp(15))
        clear.bind(on_release=lambda *_: setattr(self.inp, 'text', ''))
        paste.bind(on_release=self.paste)
        row.add_widget(clear)
        row.add_widget(paste)
        self.add_widget(row)

        res = Panel(edge=ACCENT, size_hint_y=None, height=dp(104),
                    padding=[dp(16), dp(10)], spacing=dp(4))
        res.add_widget(L('رمز التفعيل', color=MUTED, font_size=sp(13),
                         size_hint_y=None, height=dp(22)))
        self.code = L('—', shape=False, halign='center', bold=True,
                      color=ACCENT, font_size=sp(30))
        res.add_widget(self.code)
        self.add_widget(res)

        self.msg = L('', shape=False, halign='center', color=MUTED,
                     font_size=sp(14), size_hint_y=None, height=dp(24))
        self.add_widget(self.msg)

        btns = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(10),
                         padding=[dp(6), 0])
        copy = SkewButton(text='نسخ الرمز')
        copy.bind(on_release=self.copy_code)
        wa = SkewButton(text='واتساب', bg=hexc('#1FA855'),
                        bg_down=hexc('#17803F'), fg=(1, 1, 1, 1))
        wa.bind(on_release=self.send_wa)
        btns.add_widget(copy)
        btns.add_widget(wa)
        self.add_widget(btns)
        self.add_widget(BoxLayout())          # مساحة فارغة

    def clean(self):
        return ''.join(self.inp.text.split()).upper()

    def update(self, *a):
        dev = self.clean()
        self.code.text = make_code(dev) if dev else '—'
        self.msg.text = ''

    def paste(self, *a):
        try:
            self.inp.text = (Clipboard.paste() or '').strip()
        except Exception:
            self.msg.text = ar('تعذّر اللصق')

    def send_wa(self, *a):
        if not self.clean():
            return
        msg = ('رمز تفعيل حاسبة الرسوم العقارية:\n%s\n'
               'أدخله في خانة (رمز التفعيل) داخل التطبيق.' % self.code.text)
        share_whatsapp(msg, wa_phone(self.phone.text))

    def copy_code(self, *a):
        if self.clean():
            try:
                Clipboard.copy(self.code.text)
                self.msg.color = ACCENT
                self.msg.text = ar('تم نسخ الرمز')
            except Exception:
                self.msg.text = ar('تعذّر النسخ')


class KeyGenApp(App):
    title = 'IRG Keygen'

    def build(self):
        Window.clearcolor = BG
        if platform in ('win', 'linux', 'macosx'):
            Window.size = (400, 760)
        else:
            Window.softinput_mode = 'below_target'
        return KeyGen()


if __name__ == '__main__':
    KeyGenApp().run()
