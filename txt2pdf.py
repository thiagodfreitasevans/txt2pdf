#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import reportlab.lib.pagesizes
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import units
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import sys
import os


class Margins(object):
    def __init__(self, right, left, top, bottom):
        self._right = right
        self._left = left
        self._top = top
        self._bottom = bottom

    @property
    def right(self):
        return self._right * units.cm

    @property
    def left(self):
        return self._left * units.cm

    @property
    def top(self):
        return self._top * units.cm

    @property
    def bottom(self):
        return self._bottom * units.cm


class PDFCreator(object):
    appName = "txt2pdf (version 1.0)"

    def __init__(self, args, margins):
        pageWidth, pageHeight = reportlab.lib.pagesizes.__dict__[args.media]
        if args.landscape:
            pageWidth, pageHeight = reportlab.lib.pagesizes.landscape(
                (pageWidth, pageHeight))
        self.author = args.author
        self.title = args.title
        self.canvas = Canvas(args.output, pagesize=(pageWidth, pageHeight))
        self.canvas.setCreator(self.appName)
        if len(args.author) > 0:
            self.canvas.setAuthor(args.author)
        if len(args.title) > 0:
            self.canvas.setTitle(args.title)
        self.fontSize = args.font_size
        if args.font not in ('Courier'):
            self.font = 'myFont'
            pdfmetrics.registerFont(TTFont('myFont', args.font))
        else:
            self.font = args.font
        self.kerning = args.kerning
        self.margins = margins
        contentWidth = pageWidth - margins.left - margins.right
        stringWidth = self.canvas.stringWidth(
            ".", fontName=self.font, fontSize=self.fontSize)
        self.charsPerLine = int(
            (contentWidth + self.kerning) / (stringWidth + self.kerning))
        self.top = pageHeight - margins.top - self.fontSize
        self.leading = (args.extra_vertical_space + 1.2) * self.fontSize
        self.linesPerPage = int(
            (self.leading + pageHeight
             - margins.top - margins.bottom - self.fontSize) / self.leading)
        self.filename = args.filename
        self.verbose = not args.quiet

    def _readDocument(self):
        with open(self.filename, 'r') as data:
            lineno = 0
            for line in data:
                line = line.decode('utf8').rstrip('\r\n')
                lineno += 1
                if len(line) > self.charsPerLine:
                    self._scribble(
                        "Warning: wrapping line %d in %s" %
                        (lineno + 1, self.filename))
                    while len(line) > self.charsPerLine:
                        yield line[:self.charsPerLine]
                        line = line[self.charsPerLine:]
                yield line

    def _newpage(self):
        textobject = self.canvas.beginText()
        textobject.setFont(self.font, self.fontSize, leading=self.leading)
        textobject.setTextOrigin(self.margins.left, self.top)
        textobject.setCharSpace(self.kerning)
        return textobject

    def _scribble(self, text):
        if self.verbose:
            sys.stderr.write(text + os.linesep)

    def generate(self):
        self._scribble(
            "Writing '%s' with %d characters per "
            "line and %d lines per page..." %
            (self.filename, self.charsPerLine, self.linesPerPage)
        )
        data = self._readDocument()
        page, l = 1, 0
        t = self._newpage()
        for line in data:
            t.textLine(line)
            l += 1
            if l == self.linesPerPage:
                self.canvas.drawText(t)
                self.canvas.showPage()
                l = 0
                page += 1
                t = self._newpage()
        if l > 0:
            self.canvas.drawText(t)
        else:
            page -= 1
        self.canvas.save()
        self._scribble("PDF document: %d pages" % page)


parser = argparse.ArgumentParser()
parser.add_argument('filename')
parser.add_argument('--font', '-f', default='Courier',
                    help='Select a font (True Type format) by its full path')
parser.add_argument('--font-size', '-s', type=float, default=10.0,
                    help='Size of the font')
parser.add_argument('--extra-vertical-space', '-v', type=float, default=0.0,
                    help='Extra vertical space between lines')
parser.add_argument('--kerning', '-k', type=float, default=0.0,
                    help='Extra horizontal space between characters')
parser.add_argument('--media', '-m', default='A4',
                    help='Select the size of the page (A4, A3, etc.)')
parser.add_argument('--landscape', '-ls', action="store_true", default=False,
                    help='Select landscape mode')
parser.add_argument('--margin-left', '-l', type=float, default=2.0,
                    help='Left margin (in cm unit)')
parser.add_argument('--margin-right', '-r', type=float, default=2.0,
                    help='Right margin (in cm unit)')
parser.add_argument('--margin-top', '-t', type=float, default=2.0,
                    help='Top margin (in cm unit)')
parser.add_argument('--margin-bottom', '-b', type=float, default=2.0,
                    help='Bottom margin (in cm unit)')
parser.add_argument('--output', '-o', default='output.pdf',
                    help='Output file')
parser.add_argument('--author', default='',
                    help='Author of the PDF document')
parser.add_argument('--title', default='',
                    help='Title of the PDF document')
parser.add_argument('--quiet', '-q', action='store_true', default=False,
                    help='Title of the PDF document')

args = parser.parse_args()

PDFCreator(args, Margins(
    args.margin_right,
    args.margin_left,
    args.margin_top,
    args.margin_bottom)).generate()
