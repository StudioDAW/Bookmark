import freetype

DPI = 96

convert: dict[str, dict[str, float]] = {
    "pt": {
        "pt": 1,
        "px": DPI / 72,
        "mm": 25.4 / 72,
        "in": 1 / 72,
        "ft": 1 / 72 / 12
    },
    "px": {
        "pt": 72 / DPI,
        "px": 1,
        "mm": 25.4 / DPI,
        "in": 1 / DPI,
        "ft": 1 / DPI / 12
    },
    "mm": {
        "pt": 72 / 25.4,
        "px": DPI / 25.4,
        "mm": 1,
        "in": 1 / 25.4,
        "ft": 1 / 25.4 / 12
    },
    "in": {
        "pt": 72,
        "px": DPI,
        "mm": 25.4,
        "in": 1,
        "ft": 1 / 12
    },
    "ft": {
        "pt": 72 * 12,
        "px": DPI * 12,
        "mm": 25.4 * 12,
        "in": 12,
        "ft": 1
    }
}

class PageSizeDict(dict):
    def __getitem__(self, key):
        size = super().__getitem__(key)
        return PageSizeUnit(size)

class PageSizeUnit(dict):
    def __init__(self, size_pt):
        self.size_pt = size_pt

    def __getitem__(self, unit):
        if unit == "pt":
            return self.size_pt
        factor = convert["pt"].get(unit)
        if factor is None:
            raise KeyError(f"Unknown unit: {unit}")
        w_pt, h_pt = self.size_pt
        return (w_pt * factor, h_pt * factor)

pagesizes = PageSizeDict({
    'A1': (1683.7795275590554, 2383.937007874016),
    'A2': (1190.5511811023623, 1683.7795275590554),
    'A3': (841.8897637795277, 1190.5511811023623),
    'A4': (595.2755905511812, 841.8897637795277),
    'A5': (419.52755905511816, 595.2755905511812),
    'A6': (297.6377952755906, 419.52755905511816),
    'A7': (209.76377952755908, 297.6377952755906),
    'A8': (147.40157480314963, 209.76377952755908),
    'A9': (104.88188976377954, 147.40157480314963),
    'A10': (73.70078740157481, 104.88188976377954)})
    

class TextLayout:
    def __init__(self, text: str, font_path: str, font_size_pt: int):
        self.text = text
        self.font_path = font_path
        self.font_size_pt = font_size_pt
        self.face = freetype.Face(font_path)
        self.face.set_char_size(font_size_pt * 64, 0, DPI, 0)

    def width(self, text:str = "", letter_spacing: float = 0, kerning: bool = True, prev_char = None):
        text = self.text if text == "" else text
        width = 0
        for char in text:
            self.face.load_char(char)
            if kerning and prev_char:
                k = self.face.get_kerning(prev_char, char)
                width += k.x >> 6
            width += self.face.glyph.advance.x >> 6
            width += letter_spacing
            prev_char = char
        return width, prev_char

    def lines(self, max_width: float, letter_spacing: float = 0, kerning: bool = True):
        words = self.text.split(' ')
        lines = 0
        line_width = 0
        prev_char = None

        space_width, _ = self.width(" ", letter_spacing, kerning)

        for word in words:
            word_width, last_char = self.width(word, letter_spacing, kerning, prev_char)
            additional_width = word_width + (space_width if line_width > 0 else 0)

            if line_width + additional_width <= max_width:
                line_width += additional_width
            else:
                lines += 1
                line_width = word_width
            prev_char = last_char

        if line_width > 0:
            lines += 1

        return lines + len(self.text.splitlines()) - 1

    def height(self, max_width: float):
        return (self.font_size_pt * DPI / 72) * 1.2 * self.lines(max_width)
