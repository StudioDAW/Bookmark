import json
import os

CACHE_FILE = "word_cache.json"

class WordCacheManager:
    _global_cache = None

    @classmethod
    def load_cache(cls):
        if cls._global_cache is None:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r") as f:
                    cls._global_cache = json.load(f)
            else:
                cls._global_cache = {}
        return cls._global_cache

    @classmethod
    def save_cache(cls):
        if cls._global_cache is not None:
            with open(CACHE_FILE, "w") as f:
                json.dump(cls._global_cache, f, indent=2)

    @classmethod
    def get_font_cache(cls, font_key):
        cls.load_cache()
        return cls._global_cache.get(font_key, {})

    @classmethod
    def update_font_cache(cls, font_key, word_dict):
        cls.load_cache()
        cls._global_cache[font_key] = word_dict
        # Optionally defer saving to end of program
        cls.save_cache()
