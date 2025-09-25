from playwright.sync_api import sync_playwright

class PlaywrightTextMeasurer:
    def __init__(self, font=("Arial", "16")):
        self.font_family, self.font_size = font
        self.font_css = f"{self.font_size} {self.font_family}"

    def measure_line_height(self):
        height = 0
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            height = page.evaluate(f"""
                () => {{
                    const p = document.createElement('p');
                    p.style.fontFamily = '{self.font_family}';
                    p.style.fontSize = '{self.font_size}pt';
                    p.style.lineHeight = '1.2';
                    p.innerText = 'Hg';
                    document.body.appendChild(p);
                    const rect = p.getBoundingClientRect();
                    document.body.removeChild(p);
                    return rect.height;
                }}
            """)

            browser.close()
        return height

    def measure_text(self, html, id):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html)

    def measure_words(self, words):
        result = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for word in words:
                print(word)
                width = page.evaluate(f"""
                    () => {{
                        const p = document.createElement('p');
                        p.style.font = '{self.font_size}pt {self.font_family}';
                        p.innerText = {word!r};
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');
                        ctx.font = p.style.font;
                        return ctx.measureText(p.innerText).width;
                    }}
                """)
                result[word] = width
            browser.close()
        return result
