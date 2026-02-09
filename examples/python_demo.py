#!/usr/bin/env python3
"""
safe_httpeex Python Demo

Demonstrates the compiled Python API for the safe HEEx template parser.
Shows parsing, safe rendering, XSS prevention, and direct SafeHtmlBuilder usage.

Usage (from project root):
    PYTHONPATH=temper.out/py/safe-heex:temper.out/py/temper-core:temper.out/py/std \
        python3 examples/python_demo.py
"""

import sys
import os

# Add compiled Temper output to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for subdir in ["safe-heex", "temper-core", "std"]:
    sys.path.insert(0, os.path.join(project_root, "temper.out", "py", subdir))

from safe_heex_py.safe_heex import (
    parse,
    render_html,
    parse_and_render,
    render_to_debug,
    render_to_json,
    SafeHtmlBuilder,
    Text,
    Document,
)


def demo_parse_and_render():
    print("=" * 60)
    print("1. BASIC PARSE AND RENDER")
    print("=" * 60)

    template = '<div class="greeting"><p>Hello world</p></div>'
    result = parse_and_render(template)
    print(f"  Input:  {template}")
    print(f"  Output: {result}")
    print()


def demo_xss_prevention():
    print("=" * 60)
    print("2. XSS PREVENTION — THE CORE GUARANTEE")
    print("=" * 60)

    # Text nodes go through append() which auto-escapes
    malicious = "<script>alert('xss')</script>"
    doc = Document((Text(malicious, None),), None)
    result = render_html(doc)
    print(f"  Malicious input:  {malicious}")
    print(f"  Safe output:      {result}")
    print(f"  Script escaped:   {'&lt;script&gt;' in result}")
    print()


def demo_five_char_escaping():
    print("=" * 60)
    print("3. ALL 5 CHARACTERS ESCAPED")
    print("=" * 60)

    cases = [
        ("&", "&amp;",  "Ampersand"),
        ("<", "&lt;",   "Less-than"),
        (">", "&gt;",   "Greater-than"),
        ('"', "&quot;",  "Double quote"),
        ("'", "&#39;",  "Single quote"),
    ]

    all_pass = True
    for char, expected, name in cases:
        doc = Document((Text(char, None),), None)
        result = render_html(doc)
        ok = result == expected
        all_pass = all_pass and ok
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: '{char}' -> '{result}'")

    print(f"\n  All 5 chars escaped: {all_pass}")
    print()


def demo_safe_html_builder():
    print("=" * 60)
    print("4. DIRECT SafeHtmlBuilder USAGE")
    print("=" * 60)
    print("  This is the programmatic API that the renderer uses internally.")
    print("  appendSafe() = trusted template structure (no escaping)")
    print("  append()     = untrusted user content (auto-escaped)")
    print()

    builder = SafeHtmlBuilder()
    builder.append_safe('<div class="container">')
    builder.append("<script>alert('xss')</script>")  # user content
    builder.append_safe("</div>")
    result = builder.accumulated

    print(f"  appendSafe('<div class=\"container\">')")
    print(f"  append('<script>alert(\\'xss\\')</script>')  <- user content")
    print(f"  appendSafe('</div>')")
    print(f"  Result: {result}")
    print(f"  XSS blocked: {'<script>' not in result}")
    print()


def demo_ast_inspection():
    print("=" * 60)
    print("5. AST INSPECTION")
    print("=" * 60)

    template = '<div class="card"><p>Hello</p></div>'
    doc = parse(template)

    print(f"  Template: {template}")
    print(f"  Children: {len(doc.children)}")
    print()
    print("  Debug output:")
    for line in render_to_debug(doc).strip().split("\n"):
        print(f"    {line}")
    print()


if __name__ == "__main__":
    print()
    print("safe_httpeex Python Demo")
    print("Compile-time XSS prevention for HEEx templates")
    print()

    demo_parse_and_render()
    demo_xss_prevention()
    demo_five_char_escaping()
    demo_safe_html_builder()
    demo_ast_inspection()

    print("All demos completed successfully.")
