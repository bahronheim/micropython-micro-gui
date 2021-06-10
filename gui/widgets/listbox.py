# listbox.py Extension to ugui providing the Listbox class

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch
from micropython import const
from gui.core.ugui import Widget, display
from gui.core.colors import *

dolittle = lambda *_ : None

# Behaviour has issues compared to touch displays because movement between
# entries is sequential. This can affect the choice in when the callback runs.
# It always runs when select is pressed. See 'also' ctor arg.
ON_MOVE = const(1)  # Also run whenever the currency moves.
ON_LEAVE = const(2)  # Also run on exit from the control.

class Listbox(Widget):
    @staticmethod
    def dimensions(writer, elements):
        entry_height = writer.height + 2 # Allow a pixel above and below text
        le = len(elements)
        height = entry_height * le + 2
        textwidth = max(writer.stringlen(s) for s in elements) + 4
        return entry_height, height, textwidth

    def __init__(self, writer, row, col, *, elements, width=None, value=0,
                 fgcolor=None, bgcolor=None, bdcolor=False, fontcolor=None, select_color=DARKBLUE,
                 callback=dolittle, args=[], also=0):

        self.entry_height, height, textwidth = self.dimensions(writer, elements)
        self.also = also
        if width is None:
            width = textwidth
        if not isinstance(value, int) or value >= len(elements):
            value = 0
        super().__init__(writer, row, col, height, width, fgcolor, bgcolor, bdcolor, value, True)
        self.cb = callback
        self.cb_args = args
        self.select_color = select_color
        self.fontcolor = fontcolor
        fail = False
        try:
            self.elements = [s for s in elements if type(s) is str]
        except:
            fail = True
        else:
            fail = len(self.elements) == 0
        if fail:
            raise ValueError('elements must be a list or tuple of one or more strings')
        self._value = value # No callback until user selects
        self.ev = value

    def show(self):
        if not super().show(False):  # Clear to self.bgcolor
            return

        length = len(self.elements)
        x = self.col
        y = self.row
        for n in range(length):
            if n == self._value:
                display.fill_rect(x, y + 1, self.width, self.entry_height - 1, self.select_color)
                display.print_left(self.writer, x + 2, y + 1, self.elements[n], self.fgcolor, self.select_color)
            else:
                display.print_left(self.writer, x + 2, y + 1, self.elements[n], self.fgcolor, self.bgcolor)
            y += self.entry_height

    def textvalue(self, text=None): # if no arg return current text
        if text is None:
            return self.elements[self._value]
        else: # set value by text
            try:
                v = self.elements.index(text)
            except ValueError:
                v = None
            else:
                if v != self._value:
                    self.value(v)
            return v

    def do_up(self, _):
        if v := self._value:
            self.value(v - 1)
        if (self.also & ON_MOVE):  # Treat as if select pressed
            self.do_sel()

    def do_down(self, _):
        if (v := self._value) < len(self.elements) - 1:
            self.value(v + 1)
        if (self.also & ON_MOVE):
            self.do_sel()

    # Callback runs if select is pressed. Also (if ON_LEAVE) if user changes
    # list currency and then moves off the control. Otherwise if we have a
    # callback that refreshes another control, that second control does not
    # track currency.
    def do_sel(self): # Select was pushed
        self.ev = self._value
        self.cb(self, *self.cb_args)

    def enter(self):
        self.ev = self._value  # Value change detection

    def leave(self):
        if (self.also & ON_LEAVE) and self._value != self.ev:
            self.do_sel()