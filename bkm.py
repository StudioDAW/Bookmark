import os
import sys
import time
import uuid
import lorem
from layout import TextLayout, convert, pagesizes
from parser import interpret
from typing import Literal, get_type_hints, Union, Tuple
import freetype
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DPI = 96

class Size:
    def __init__(self, element):
        self.element = element

    def __getitem__(self, index):
        if index == 0:
            return float(self.element.style.get("width", "0").replace("mm",""))
        elif index == 1:
            return float(self.element.style.get("height", "0").replace("mm",""))
        else:
            raise IndexError

    def __setitem__(self, index, value):
        if index == 0:
            self.element.style["width"] = f"{value}mm"
        elif index == 1:
            self.element.style["height"] = f"{value}mm"
        else:
            raise IndexError

    def __repr__(self):
        return f"[{self[0]}, {self[1]}]"

class HTMLElement:
    def __init__(self, tag="div", classname="", style=None, content=None, id=None):
        self._tag = tag
        self._classname = classname
        self._style = style if style else {}
        self._children = {}  # id -> HTMLElement or string
        self._id = id if id else str(uuid.uuid4())

        # add initial content if provided
        if content:
            if isinstance(content, dict):
                for name, child in content.items():
                    self.append(child, name)
            else:
                self.append(content)

    @property
    def id(self):
        return self._id

    @property
    def classname(self):
        return self._classname

    @classname.setter
    def classname(self, value):
        self._classname = value

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, value):
        self._style = value

    @property
    def size(self):
        return Size(self)

    @size.setter
    def size(self, value):
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("size must be a list or tuple of [width, height]")
        self._style["width"] = f"{value[0]}mm"
        self._style["height"] = f"{value[1]}mm"

    @property
    def children(self):
        return self._children

    def append(self, element, name=None):
        """Append a child (HTMLElement or string)."""
        if isinstance(element, str):
            child_id = name if name else str(uuid.uuid4())
            self._children[child_id] = element
            return child_id

        if isinstance(element, HTMLElement):
            child_id = name if name else element.id
            self._children[child_id] = element
            return element.id

        raise TypeError("Child must be HTMLElement or string")

    def __str__(self):
        style_str = "; ".join(f"{k}: {v}" for k, v in self._style.items())
        children_str = "".join(str(c) for c in self._children.values())
        return f'<{self._tag} id="{self._id}" class="{self._classname}" style="{style_str}">{children_str}</{self._tag}>'

    def __repr__(self):
        return str(self)

    def __add__(self, other):
        return str(self) + str(other)

    def __radd__(self, other):
        return str(other) + str(self)


# Shortcut classes
class Div(HTMLElement):
    def __init__(self, classname="", style=None, content=None, id=None):
        super().__init__("div", classname, style, content, id)

class Body(HTMLElement):
    def __init__(self, classname="", style=None, content=None, id=None):
        super().__init__("body", classname, style, content, id)
        
class P(HTMLElement):
    def __init__(self, classname="", style=None, content=None, id=None):
        super().__init__("p", classname, style, content, id)


class BKM:
    def __init__(self):
        self.view = Body("view", style={"margin": "0", "display": "grid", "columns": "1", "justify-content": "center", "column-gap": "1px", "row-gap": "50px", "background-color": "#262626"})
        self.spreads = []
        self.pages: list[HTMLElement] = []
        self.settings()

    def document(self,
                 unit:      Literal["mm","px","pt","in","ft"] = "mm",
                 size:      Literal["A1","A2","A3","A4","A5","A6","A7","A8","A10"] = "A4",
                 width:     float | None = None,
                 height:    float | None = None,
                 spread:    bool = True,
                 start:     Literal["left","right"] = "right",
                 # margin:    Union[int, float, Tuple[int|float, ...]] = (25,25,30,25),
                 margin:    Tuple[int|float, ...] = (25,25,30,25),
                 bleed:     Tuple[int|float, ...] = (3,)):
        w, h = pagesizes[size][unit]
        if width is not None: w = width
        if height is not None: h = height
        self.size = (w,h)
        self.unit = unit
        self.spread = spread
        self.start = start
        self.margin = margin
        self.margin = self.csstuple(margin)
        self.bleed = self.csstuple(bleed)


        if self.spread:
            self.view.style["grid-template-columns"] = "repeat(2, max-content)"

    def settings(self, guides: bool = True):
        self.guides = guides

    def csstuple(self, values):
        if len(values) == 1:
            t = r = b = l = values[0]
        elif len(values) == 2:
            t, r = values
            b, l = t, r
        elif len(values) == 3:
            t, r, b = values
            l = r
        elif len(values) == 4:
            t, r, b, l = values
        else:
            raise ValueError("CSS shorthand must have 1–4 values")

        return (t, r, b, l)

    # LEFT / RIGHT VARIABLES FOR EACH PAGE    
    # INNER / OUTER MARGIN
    def page(self):
        page = Div("page", style={"width": f"{self.size[0]+self.bleed[1]+self.bleed[3]}{self.unit}", "height": f"{self.size[1]+self.bleed[0]+self.bleed[2]}{self.unit}", "background-color": "white", "position": "relative", "padding": " ".join([f"{m+self.bleed[i]}{self.unit}" for i, m in enumerate(self.margin)]), "box-sizing": "border-box", "line-height": "1.2"})
        self.pages.append(page)
        self.cursor_y = self.margin[0]+self.bleed[0]

    def paragraph(self, content: str, width: float = 1.0, font: tuple[str,int] = ("Helvetica", 20)):
        print(font)
        default_width = self.size[0] - self.margin[1] - self.margin[3]
        if width == 1.0:
            width = default_width
        elif width < 1 and width > 0:
            width *= default_width
        elif width < 0:
            width += default_width

        layout = TextLayout(content, "/System/Library/Fonts/Helvetica.ttc", font[1])

        height = layout.height(max_width=width * convert[self.unit]["px"])

        print(height, height * convert["px"][self.unit])
        self.cursor_y += height * convert["px"][self.unit]

        newpage = False
        print("y:",self.cursor_y)
        print("s:",self.size[1]  - self.margin[2] + self.bleed[2])
        if self.cursor_y > self.size[1] - self.margin[2] + self.bleed[0] + self.bleed[2]:
            diff = self.cursor_y - (self.size[1] - self.margin[2] + self.bleed[0] + self.bleed[2])
            line_height = font[1] * convert["pt"]["px"] * 1.2
            lines = int((diff * convert[self.unit]["px"]) / line_height)
            split = content.splitlines()
            self.cursor_y -= height * convert["px"][self.unit] + line_height
            self.paragraph("\n".join(split[:len(split)-lines]), font=font)
            self.page()
            content = "\n".join(split[len(split)-lines:])

        content = "</br>".join(content.splitlines())
        paragraph = P("paragraph",
                      style={"margin-top": "0",
                             "font-family": font[0],
                             "font-size": f"{layout.font_size_pt}pt",
                             "text-align": "justify",
                             "font-kerning": "none"})
        paragraph.style["width"] = str(width)+self.unit
        paragraph.append(content)
        self.pages[-1].append(paragraph)

    def lorem(self, paragraphs=1, width=1):
        for i in range(paragraphs):
            self.paragraph(lorem.paragraph(), width)

    def write(self):
        print(self.margin)
        if self.spread and self.start == "right":
            self.pages[0].style["grid-column"] = "2"
        if self.guides:
            for page in self.pages:
                page.append(Div("guide", {"position": "absolute", "outline": "1px solid blue", "inset": " ".join([f"{m+self.bleed[i]}mm" for i, m in enumerate(self.margin)])}))
                page.append(Div("guide", {"position": "absolute", "outline": "1px solid darkgrey", "inset": " ".join([f"{b}mm" for b in self.bleed])}))
        for page in self.pages:
            self.view.append(page)
        with open("index.html", "w") as f:
            f.write('<script src="http://localhost:35729/livereload.js"></script>'+str(self.view))



class FileWatcher(FileSystemEventHandler):
    def __init__(self, path):
        self.path = path

    def on_modified(self, event):
        if event.src_path.endswith(self.path):
            python = sys.executable
            os.execv(python, [python] + sys.argv)

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

if __name__ == "__main__":
    with open("document.bkm", "r") as f:
        interpret(BKM(), f.read())
    # with open("index.html", "r") as f:
    #     print(f.read())
    loop("document.bkm")
