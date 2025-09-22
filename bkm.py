import uuid
from parser import interpret
from typing import Literal, get_type_hints, Union, Tuple

pagesizes = {
    'A1': {"pt": (1683.7795275590554, 2383.937007874016)},
    'A2': {"pt": (1190.5511811023623, 1683.7795275590554)},
    'A3': {"pt": (841.8897637795277, 1190.5511811023623)},
    'A4': {"pt": (595.2755905511812, 841.8897637795277)},
    'A5': {"pt": (419.52755905511816, 595.2755905511812)},
    'A6': {"pt": (297.6377952755906, 419.52755905511816)},
    'A7': {"pt": (209.76377952755908, 297.6377952755906)},
    'A8': {"pt": (147.40157480314963, 209.76377952755908)},
    'A9': {"pt": (104.88188976377954, 147.40157480314963)},
    'A10': {"pt": (73.70078740157481, 104.88188976377954)}
}

units = {
    "mm": 25.4 / 72,
    "px": 1,
    "in": 1 / 72,
    "ft": 1 / 72 / 12
}

for unit, convert in units.items():
    for sizetype, size in pagesizes.items():
        size[unit] = (size["pt"][0] * convert, size["pt"][1] * convert)



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

# Create main doc
# view = Body("view", style={"margin": "0", "display": "flex", "flex-direction": "column", "align-items": "center", "gap": "10px", "background-color": "#262626"})
#
# pages = []
#
# for i in range(10):
#     pages.append(Div("page", style={"width": "210mm", "height": "297mm", "background-color": "white"}))
#
#     para = Div("paragraph", style={"font-size": "16pt"})
#     para.append(f"This is a page {i}")
#
#     pages[i].append(para)
#
#     pages[i].children[para.id].style["font-family"] = "Arial"
#
# for page in pages:
#     view.append(page)
#
# print(view)
#
# with open("output.html", "w") as f: f.write(str(view))

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
        page = Div("page", style={"width": f"{self.size[0]+self.bleed[1]+self.bleed[3]}{self.unit}", "height": f"{self.size[1]+self.bleed[0]+self.bleed[2]}{self.unit}", "background-color": "white", "position": "relative"})
        self.pages.append(page)

    def paragraph(self, content):
        para = Div("paragraph", style={"font-size": "16pt"})
        para.append(content)
        self.pages[-1].append(para)

    def write(self):
        print(self.margin)
        if self.spread and self.start == "right":
            self.pages[0].style["grid-column"] = "2"
        if self.guides:
            for page in self.pages:
                page.append(Div("guide", {"position": "absolute", "border": "1px solid blue", "inset": " ".join([f"{m+self.bleed[i]}mm" for i, m in enumerate(self.margin)])}))
                page.append(Div("guide", {"position": "absolute", "border": "1px solid darkred", "inset": " ".join([f"{b}mm" for b in self.bleed])}))
        for page in self.pages:
            self.view.append(page)
        with open("output.html", "w") as f:
            f.write(str(self.view))


if __name__ == "__main__":
    with open("document.bkm", "r") as f:
        interpret(BKM(), f.read())
    with open("output.html", "r") as f:
        print(f.read())
