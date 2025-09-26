#!/usr/bin/env python3
"""
Word-Position Based Line Detection using Playwright
Uses word-level position detection for accurate line breaks
"""

import asyncio
from playwright.async_api import async_playwright
import argparse
import json
from pathlib import Path
from typing import List, Dict

JS_LINE_EXTRACTOR = """
(element) => {
    const clone = element.cloneNode(true);
    clone.style.position = 'absolute';
    clone.style.visibility = 'hidden';
    clone.style.top = '-10000px';
    clone.style.width = getComputedStyle(element).width; // preserve layout width
    document.body.appendChild(clone);

    try {
        const walker = document.createTreeWalker(clone, NodeFilter.SHOW_TEXT, null, false);
        const wordRects = [];
        let node;

        while (node = walker.nextNode()) {
            const text = node.textContent;
            if (!text) continue;

            // Split text into words but keep spaces
            const words = text.split(/(\\s+)/);
            let charOffset = 0;

            for (let w of words) {
                if (!w) continue;

                const range = document.createRange();
                range.setStart(node, charOffset);
                range.setEnd(node, charOffset + w.length);
                charOffset += w.length;

                const rects = Array.from(range.getClientRects());
                for (const r of rects) {
                    if (r.width > 0 && r.height > 0) {
                        wordRects.push({ word: w, top: r.top, left: r.left, height: r.height });
                    }
                }
            }
        }

        if (wordRects.length === 0) {
            return [element.textContent.trim()];
        }

        // Sort by vertical position first
        wordRects.sort((a, b) => a.top - b.top);

        // Group words into lines based on vertical midpoint
        const tolerance = 3; // pixels
        const linesGroups = [];
        let currentLine = [];
        let currentMid = null;

        for (const w of wordRects) {
            const midY = w.top + w.height / 2;
            if (currentMid === null || Math.abs(midY - currentMid) > tolerance) {
                if (currentLine.length) linesGroups.push(currentLine);
                currentLine = [w];
                currentMid = midY;
            } else {
                currentLine.push(w);
            }
        }
        if (currentLine.length) linesGroups.push(currentLine);

        // Sort words within each line by horizontal position
        const lines = linesGroups.map(lineWords => {
            lineWords.sort((a, b) => a.left - b.left);
            return lineWords.map(w => w.word).join('');
        });

        return lines;

    } finally {
        document.body.removeChild(clone);
    }
}
"""

async def get_rendered_paragraph_lines(html_file: str, headless: bool = True) -> Dict[str, List[str]]:
    """Extract actual rendered lines by analyzing word positions in browser layout"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        try:
            file_path = Path(html_file).resolve()
            await page.goto(f"file://{file_path}")
            await page.wait_for_load_state('networkidle')

            paragraphs = await page.query_selector_all('p')
            result = {}

            for i, paragraph in enumerate(paragraphs):
                lines = await page.evaluate(JS_LINE_EXTRACTOR, paragraph)
                if lines and len(lines) > 0:
                    result[f"paragraph_{i+1}"] = lines

            return result

        except Exception as e:
            print(f"Error processing {html_file}: {e}")
            return {}

        finally:
            await browser.close()


async def get_specific_paragraph_lines(html_file: str, selector: str, headless: bool = True) -> List[str]:
    """Extract rendered lines from a specific paragraph using word-position detection"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        try:
            file_path = Path(html_file).resolve()
            await page.goto(f"file://{file_path}")
            await page.wait_for_load_state('networkidle')

            paragraph = await page.query_selector(selector)
            if not paragraph:
                print(f"No element found with selector: {selector}")
                return []

            lines = await page.evaluate(JS_LINE_EXTRACTOR, paragraph)
            return lines

        except Exception as e:
            print(f"Error processing specific paragraph: {e}")
            return []

        finally:
            await browser.close()


def print_results(results: Dict[str, List[str]]):
    """Pretty print the extracted lines"""
    if not results:
        print("No paragraphs found.")
        return

    for paragraph_key, lines in results.items():
        print(f"\n{'='*60}")
        print(f"{paragraph_key.upper()} ({len(lines)} visual lines)")
        print('='*60)

        for i, line in enumerate(lines, 1):
            print(f"{i:2d}: {line}")


async def main():
    parser = argparse.ArgumentParser(description="Extract lines using word-position detection")
    parser.add_argument("html_file", help="Path to HTML file")
    parser.add_argument("--selector", "-s", help="CSS selector for specific paragraph")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--visible", "-v", action="store_true", help="Run browser in visible mode")

    args = parser.parse_args()

    if not Path(args.html_file).exists():
        print(f"Error: File '{args.html_file}' does not exist.")
        return

    headless = not args.visible

    if args.selector:
        lines = await get_specific_paragraph_lines(args.html_file, args.selector, headless)
        results = {"selected_paragraph": lines}

        if not args.output:
            print(f"Visual lines from '{args.selector}' ({len(lines)} lines):")
            for i, line in enumerate(lines, 1):
                print(f"{i:2d}: {line}")
    else:
        results = await get_rendered_paragraph_lines(args.html_file, headless)

        if not args.output:
            print_results(results)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {args.output}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        asyncio.run(main())
    else:
        print("Usage examples:")
        print("python script.py file.html")
        print("python script.py file.html --selector 'p.article-content'")
        print("python script.py file.html --output results.json")
        print("python script.py file.html --visible")
        print("\nUses word-level position detection for accurate line breaks")
