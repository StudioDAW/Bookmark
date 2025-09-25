import uuid

class HTMLElement:
    def __init__(self, tag="div", classname="", style=None, content=None, id=None):
        self._tag = tag
        self._classname = classname
        self._style = style if style else {}
        self._children = {}  
        self._id = id if id else str(uuid.uuid4())

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
    def children(self):
        return self._children

    def append(self, element, name=None):
        """Append a child (HTMLElement or string). Ensure it's a proper Unicode string."""
        if isinstance(element, bytes):
            element = element.decode("utf-8")
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


class Div(HTMLElement):
    def __init__(self, classname="", style=None, content=None, id=None):
        super().__init__("div", classname, style, content, id)

class Body(HTMLElement):
    def __init__(self, classname="", style=None, content=None, id=None):
        super().__init__("body", classname, style, content, id)
        
class P(HTMLElement):
    def __init__(self, classname="", style=None, content=None, id=None):
        super().__init__("p", classname, style, content, id)
