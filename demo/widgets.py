import hashlib
import json
import os
import subprocess
import textwrap
import zipfile
from datetime import datetime
from math import atan2, pi, cos, sin, ceil

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, Gio, GdkPixbuf, GLib


COLORS = {
    'R': '#ef2929',
    'G': '#73d216',
    'Y': '#fce94f',
    'O': '#fcaf3e',
    'P': '#ad7fa8',
    'B': '#729fcf',
    'K': '#000000',
    'A': '#888a85',
    'C': '#17becf',
    'W': '#ffffff',
    'M': '#88419d'
}

def pix(v):
    """Round to neareast 0.5 for cairo drawing"""
    x = round(v * 2)
    return x / 2 if x % 2 else (x + 1) / 2

class ColorSequence(object):
    def __init__(self, sequence):
        self.values = [self.parse(COLORS.get(v, '#000000')) for v in sequence]

    def __call__(self, value, alpha=1.0):
        if value < len(self.values):
            col = self.values[value].copy()
            col.alpha = alpha
        else:
            col = self.values[-1].copy()
            col.alpha = alpha
        return col

    @staticmethod
    def parse(spec):
        col = Gdk.RGBA()
        col.parse(spec)
        return col


class DemoByte(Gtk.Widget):
    __gtype_name__ = 'DemoByte'
    value = GObject.Property(type=int, default=0, nick='Display Value')
    offset = GObject.Property(type=int, minimum=0, maximum=4, default=0, nick='Byte Offset')
    count = GObject.Property(type=int, minimum=1, maximum=8, default=8, nick='Byte Count')
    big_endian = GObject.Property(type=bool, default=False, nick='Big-Endian')
    labels = GObject.Property(type=str, default='', nick='Labels')
    colors = GObject.Property(type=str, default="AG", nick='Value Colors')
    columns = GObject.Property(type=int, minimum=1, maximum=8, default=1, nick='Columns')
    size = GObject.Property(type=int, minimum=5, maximum=50, default=10, nick='LED Size')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._view_bits = ['0'] * self.count
        self._view_labels = [''] * self.count
        self.palette = ColorSequence(self.colors)
        self.set_size_request(200, 200)
        for prop in ['value', 'offset', 'count', 'big-endian', 'labels', 'colors', 'columns', 'size']:
            self.connect('notify::{}'.format(prop), self.on_notify)
        
    def do_realize(self):
        allocation = self.get_allocation()
        attr = Gdk.WindowAttr()
        attr.window_type = Gdk.WindowType.CHILD
        attr.x = allocation.x
        attr.y = allocation.y
        attr.width = allocation.width
        attr.height = allocation.height
        attr.visual = self.get_visual()
        attr.event_mask = self.get_events() | Gdk.EventMask.EXPOSURE_MASK
        mask = Gdk.WindowAttributesType.X | Gdk.WindowAttributesType.Y | Gdk.WindowAttributesType.VISUAL
        window = Gdk.Window(self.get_parent_window(), attr, mask);
        self.set_window(window)
        self.register_window(window)
        self.set_realized(True)
        window.set_background_pattern(None)
        self.on_notify(None, None)


    def do_draw(self, cr):
        allocation = self.get_allocation()
        stride = ceil(self.count / self.columns)
        col_width = allocation.width / self.columns

        line_color = self.get_style_context().get_color(Gtk.StateFlags.NORMAL)

        # draw boxes
        cr.set_line_width(0.75)

        for i in range(self.count):
            x = pix((i // stride) * col_width + 4)
            y = pix(4 + (i % stride) * (self.size + 5))
            cr.rectangle(x, y, self.size, self.size)
            color = self.palette(int(self._view_bits[i]))
            cr.set_source_rgba(*color)
            cr.fill_preserve()
            cr.set_source_rgba(*line_color)
            cr.stroke()

            # draw label
            cr.set_source_rgba(*line_color)
            label = self._view_labels[i]
            xb, yb, w, h = cr.text_extents(label)[:4]
            cr.move_to(x + self.size + 4.5, y + self.size / 2 - yb - h / 2)
            cr.show_text(label)
            cr.stroke()

    def on_notify(self, widget, pspec):
        """
        Redraw when properties change
        """

        # bits
        bits = list(bin(self.value)[2:].zfill(64))
        if self.big_endian:
            self._view_bits = bits[self.offset:][:self.count]
        else:
            self._view_bits = bits[::-1][self.offset:][:self.count]

        # colors
        self.palette = ColorSequence(self.colors)

        # labels
        labels = [v.strip() for v in self.labels.split(',')]
        self._view_labels = labels + (self.count - len(labels)) * ['']

        self.queue_draw()


