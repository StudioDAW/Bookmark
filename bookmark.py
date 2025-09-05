import enum
from reportlab.lib.pagesizes import *
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
import re
import inspect
from typing import Literal
import os, sys
import getpass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import lorem


class BookmarkError(Exception):
    def __init__(self, field:str, message:str):
        self.field, self.message = field, message
        super().__init__(f"[{field}] {message}")


class FileWatcher(FileSystemEventHandler):
    def __init__(self, path):
        self.path = path

    def on_modified(self, event):
        if event.src_path.endswith(self.path):
            python = sys.executable
            os.execv(python, [python] + sys.argv)


class Font(str):
    size: int
    bold: str|None
    italic: str|None


class Document:
    def __init__(self, path:str=sys.argv[1]) -> None:
        self.path = path
        self.parser = Parser(self)
        if os.path.isdir(self.path):
            print("structure")
        elif os.path.isfile(self.path):
            with open(self.path, "r") as f:
                self.parser.parse(f.readlines())
            self.canvas.save()
            # os.system(f"open {self.filename}")
        else:
            raise BookmarkError("Document.path", f"No such file or directory: {self.path}")

    def document(self, title:str="Document", author:str=getpass.getuser(), size:Literal["A1","A2","A3","A4","A5","A6","A7","A8","A9","A10"]="A4"):
        self.filename = "output.pdf"
        self.title = title
        self.author = author
        self.pagesize = {"A1":A1,"A2":A2,"A3":A3,"A4":A4,"A5":A5,"A6":A6,"A7":A7,"A8":A8,"A9":A9,"A10":A10}[size]
        self.canvas = canvas.Canvas(self.filename, self.pagesize)
        self.margin = (0, 0, 0, 0)
        self.font = Font("Helvetica")
        self.font.bold = "Helvetica-Bold"
        self.font.size = 12
        self.initfont("Zapf", "~/Library/Fonts/Zapf Dingbats Regular.ttf")
        self.cursor_y = self.pagesize[1]

    def setmargin(self, top=None, right=None, bottom=None, left=None, vertical=None, horizontal=None, all=None):
        if all is not None:
            vals = [all] * 4
        else:
            vals = list(self.margin)

            if vertical is not None:
                vals[0] = vals[2] = vertical
            if horizontal is not None:
                vals[1] = vals[3] = horizontal

            if top is not None: vals[0] = top
            if right is not None: vals[1] = right
            if bottom is not None: vals[2] = bottom
            if left is not None: vals[3] = left

        self.margin = tuple(vals)
        self.cursor_y = self.pagesize[1] - self.margin[0]

    def initfont(self, name: str, path: str):
        pdfmetrics.registerFont(TTFont(name, os.path.expanduser(path)))

    def setfont(self, name: str|Font, size: int=12, bold=None, italic=None):
        if isinstance(name, Font):
            self.font = name
        else:
            self.font = Font(name)
            self.font.size = size
            self.font.bold = self.font if bold==None else bold
            self.font.italic = self.font if italic==None else italic
        self.canvas.setFont(self.font, self.font.size)

    def newpage(self):
        self.canvas.showPage()

    def heading(self, text="Heading", level=2):
        text = text.replace("\n","")
        fontsize = {1: 24, 2: 18, 3: 14}[level]
        leading = fontsize * 1.2
        gap_above = leading * 1.5
        gap_below = leading * 1
        
        self.cursor_y -= gap_above
        self.canvas.setFont(self.font.bold, fontsize)
        self.canvas.drawString(self.margin[3], self.cursor_y, text)
        self.cursor_y -= gap_below

        self.canvas.setFont(self.font, self.font.size)

    def split(self, text):
        buffer = []
        self.paragraph("")
        for i, line in enumerate(text.splitlines()):
            if i % 2 == 1:
                buffer.append(line)
            else:
                self.paragraph(line, nogap=True)

        self.newpage()

        self.setfont(self.font)

        self.cursor_y = self.pagesize[1]-self.margin[0]
        self.paragraph("")

        for line in buffer:
            self.paragraph(line, nogap=True)


    def paragraph(self, text=None, leading=None, justified=True, parspacing=0, nogap=False):
        if text == None:
            text = lorem.paragraph()
        if leading is None:
            leading = int(self.font.size * 1.2)

        x = self.margin[3]
        width = self.pagesize[0] - self.margin[3] - self.margin[1]
        space_base = self.canvas.stringWidth(" ", self.font, self.font.size)

        text += "\n" if not nogap else ""

        for raw_line in (text).split("\n"):
            words = raw_line.split()

            if not words:
                self.cursor_y -= leading
                continue
            else:
                words[0] = " "*raw_line.find(words[0]) + words[0]

            lines, current_line, current_width = [], [], 0
            for word in words:
                w = self.canvas.stringWidth(word, self.font, self.font.size)
                test_width = current_width + (space_base if current_line else 0) + w
                if test_width <= width:
                    current_line.append(word)
                    current_width = test_width
                else:
                    lines.append(current_line)
                    current_line, current_width = [word], w
            if current_line:
                lines.append(current_line)

            for i, line in enumerate(lines):
                if self.cursor_y - leading < self.margin[2]:
                    self.newpage()

                if not justified or len(line) == 1 or i == len(lines) - 1:
                    self.canvas.drawString(x, self.cursor_y, " ".join(line))
                else:
                    word_widths = [self.canvas.stringWidth(w, self.font, self.font.size) for w in line]
                    total_words_width = sum(word_widths)
                    gaps = len(line) - 1
                    natural_space = gaps * space_base
                    extra_space = (width - total_words_width - natural_space) / gaps
                    cursor = x
                    for j, w in enumerate(line):
                        self.canvas.drawString(cursor, self.cursor_y, w)
                        cursor += word_widths[j]
                        if j < gaps:
                            cursor += space_base + extra_space
                self.cursor_y -= leading

        self.cursor_y -= parspacing

    def list(self, text="", leading=None):
        default_font = self.font
        symbol_width = pdfmetrics.stringWidth(chr(111), "Zapf", 12)
        indent = "       "
        if leading is None:
            leading = int(self.font.size * 1.2)

        for i, line in enumerate(text.splitlines()):
            # if i == 0:
            #     char = chr(52)
            # else: char = chr(111)
            if self.cursor_y - leading < self.margin[2]:
                self.newpage()
            self.setfont("Zapf")
            self.canvas.drawString(self.margin[3], self.cursor_y, indent+chr(111))
            self.setfont(default_font)
            line = line.replace("-",indent,1)
            self.canvas.drawString(self.margin[3], self.cursor_y, line)
            self.cursor_y -= leading

        self.cursor_y -= leading

        # levels = []
        # for line in text.splitlines():
        #     indent = len(line.split("-",1)[0])
        #     if indent not in levels: levels.append(indent)
        #     if len(levels) > 1:
        #         if 





    def rectangle(self, x=0, y=0, width=50, height=50, stroke=1, fill=0):
        self.canvas.rect(x, y, width, height, stroke, fill)


"""
Rewrite Parser to handle args better 
"""
class Parser:
    def __init__(self, doc:Document):
        self.doc = doc

        self.methods = {name: method for name, method in inspect.getmembers(Document, predicate=inspect.isfunction)}

    def parse_args(self, arg_str):
        if not arg_str:
            return {}

        pattern = re.compile(r'(\w+)\s*=\s*(?:"(.*?)"|\'(.*?)\'|([^\s,]+))')
        args = {}

        for match in pattern.finditer(arg_str):
            key = match.group(1)
            value = (match.group(2) or match.group(3) or match.group(4)).strip()

            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass

            args[key] = value

        return args

    def parse(self, lines):
        current_command = None
        current_args = {}
        buffer = []

        for line in lines:
            line = line.rstrip()

            if line.startswith(";"):
                if current_command and buffer:
                    if buffer[-1] == "": buffer.pop()
                    getattr(self.doc, current_command)("\n".join(buffer), **current_args)
                    buffer = []
                    current_args = {}
                    current_command = None

                is_block = ":" in line
                parts = line[1:].split("(", 1)
                cmd = parts[0].strip()

                if cmd not in self.methods:
                    continue

                arg_str = ""
                content_after_colon = ""
                if len(parts) > 1:
                    rest = parts[1]
                    if is_block:
                        if "):" in rest:
                            arg_str, after = rest.split("):", 1)
                            content_after_colon = after.strip()
                        elif rest.endswith(":"):
                            arg_str = rest[:-1]
                        else:
                            arg_str = rest.rstrip(")")
                    else:
                        arg_str = rest.rstrip(")")

                current_args = self.parse_args(arg_str)

                if is_block:
                    current_command = cmd
                    if content_after_colon:
                        buffer.append(content_after_colon)
                else:
                    getattr(self.doc, cmd)(**current_args)
                    current_command = None
                continue

            if current_command:
                buffer.append(line)

        if current_command and buffer:
            if buffer[-1] == "": buffer.pop()
            getattr(self.doc, current_command)("\n".join(buffer), **current_args)



def loop(path):
    observer = Observer()
    observer.schedule(FileWatcher(path), path=os.path.dirname(os.path.abspath(path)) or ".", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
