# metrics.py
from .measurer import PlaywrightTextMeasurer
from .cache_manager import WordCacheManager

class TextMetrics:
    def __init__(self, font=("Arial","16pt")):
        self.font_family, self.font_size = font
        self.font_key = f"{self.font_family}_{self.font_size}"
        self.measurer = PlaywrightTextMeasurer(font)
        self.word_cache = WordCacheManager.get_font_cache(self.font_key)

    def line_height(self):
        return self.measurer.measure_line_height()

    def measure_words(self, words:list[str]):
        words.append(" ")
        result = {cached: width for cached, width in self.word_cache.items()}
        for word, width in self.measurer.measure_words([w for w in words if w not in self.word_cache]).items():
            result[word] = width
            self.word_cache[word] = width
        space_width = result.pop(words.pop())

        WordCacheManager.update_font_cache(self.font_key, self.word_cache)
        return (result, space_width)
