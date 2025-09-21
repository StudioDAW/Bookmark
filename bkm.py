import uuid
from parser import interpret

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
        self.view = Body("view", style={"margin": "0", "display": "flex", "flex-direction": "column", "align-items": "center", "gap": "10px", "background-color": "#262626"})
        self.pages = []

    def document(self):
        pass

    def page(self, size):
        page = Div("page", style={"background-color": "white"})
        page.size = size
        self.pages.append(page)

    def paragraph(self, content):
        para = Div("paragraph", style={"font-size": "16pt"})
        para.append(content)
        self.pages[-1].append(para)

    def write(self):
        for page in self.pages: self.view.append(page)
        with open("output.html", "w") as f:
            f.write(str(self.view))


if __name__ == "__main__":
    with open("document.bkm", "r") as f:
        interpret(BKM(), f.read())
    with open("output.html", "r") as f:
        print(f.read())
