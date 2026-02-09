#!/usr/bin/env python3
"""
safe_httpeex Django Integration Example

Shows how to integrate the safe HEEx parser with Django.
The Django template tag code is commented out (requires Django installed).
A standalone demo at the bottom runs without Django to show the concepts.

Integration approach:
  1. Custom template tag:  {% heex "<div>{@name}</div>" %}
  2. Custom template filter: {{ template_string|heex }}
  3. SafeHtmlBuilder for programmatic safe HTML in views

Usage (standalone demo, from project root):
    PYTHONPATH=temper.out/py/safe-heex:temper.out/py/temper-core:temper.out/py/std \
        python3 examples/django_integration.py
"""

# ============================================================
# Django Template Tags (requires Django)
# ============================================================
#
# Save this as yourapp/templatetags/heex_tags.py:
#
# from django import template
# from django.utils.safestring import mark_safe
# from safe_heex_py.safe_heex import parse_and_render, SafeHtmlBuilder
#
# register = template.Library()
#
#
# @register.simple_tag
# def heex(template_string):
#     """
#     Parse and render a HEEx template string safely.
#
#     Usage in Django template:
#         {% load heex_tags %}
#         {% heex '<div class="greeting"><p>Hello</p></div>' %}
#
#     Why mark_safe is correct here:
#         SafeHtmlBuilder internally escapes ALL untrusted content via
#         append(). By the time we get the rendered string, every user-
#         facing value has already been HTML-escaped. The template
#         structure (tags, attribute names) passes through appendSafe()
#         because it comes from the parsed template source, not user input.
#     """
#     return mark_safe(parse_and_render(template_string))
#
#
# @register.filter(name="heex")
# def heex_filter(value):
#     """
#     Template filter for rendering HEEx strings.
#
#     Usage:
#         {{ my_template_var|heex }}
#     """
#     return mark_safe(parse_and_render(value))
#
#
# @register.simple_tag
# def safe_html(content, tag="div", css_class=""):
#     """
#     Build safe HTML programmatically using SafeHtmlBuilder.
#
#     Usage:
#         {% safe_html user_input tag="p" css_class="user-content" %}
#
#     The content parameter is untrusted (auto-escaped via append).
#     The tag and css_class are trusted template parameters (appendSafe).
#     """
#     builder = SafeHtmlBuilder()
#     builder.append_safe(f"<{tag}")
#     if css_class:
#         builder.append_safe(f' class="{css_class}"')
#     builder.append_safe(">")
#     builder.append(str(content))  # untrusted — auto-escaped
#     builder.append_safe(f"</{tag}>")
#     return mark_safe(builder.accumulated)


# ============================================================
# Standalone Demo (runs without Django)
# ============================================================

if __name__ == "__main__":
    import sys
    import os

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for subdir in ["safe-heex", "temper-core", "std"]:
        sys.path.insert(0, os.path.join(project_root, "temper.out", "py", subdir))

    from safe_heex_py.safe_heex import parse_and_render, SafeHtmlBuilder

    print()
    print("Django Integration Concepts Demo")
    print("(runs without Django to show the concepts)")
    print()

    # 1. Template tag simulation
    print("1. Template tag: {% heex template_string %}")
    print("-" * 50)
    template = '<div class="user-card"><h2>Welcome</h2><p>Content here</p></div>'
    result = parse_and_render(template)
    print(f"  Input:  {template}")
    print(f"  Output: {result}")
    print(f"  (In Django, wrapped in mark_safe() — safe because renderer")
    print(f"   already escaped all untrusted content via SafeHtmlBuilder)")
    print()

    # 2. SafeHtmlBuilder for user content in views
    print("2. Safe HTML builder: {% safe_html user_input %}")
    print("-" * 50)
    user_input = '<img src=x onerror="alert(document.cookie)">'
    builder = SafeHtmlBuilder()
    builder.append_safe('<div class="user-content">')
    builder.append(user_input)  # untrusted — auto-escaped
    builder.append_safe("</div>")
    result = builder.accumulated
    print(f"  User input:   {user_input}")
    print(f"  Safe output:  {result}")
    print(f"  XSS blocked:  {'<img' not in result}")
    print()

    # 3. Why mark_safe is appropriate
    print("3. Why mark_safe() is correct with SafeHtmlBuilder")
    print("-" * 50)
    print("  SafeHtmlBuilder enforces safety at BUILD time:")
    print("    appendSafe(s) -> trusted template structure, no escaping")
    print("    append(s)     -> untrusted user content, auto-escaped")
    print("    .accumulated  -> final string, ALL user content already escaped")
    print()
    print("  Django's mark_safe() says 'this string is already safe.'")
    print("  That's correct here because SafeHtmlBuilder guarantees it.")
    print("  The safety is structural, not a promise — append() ALWAYS escapes.")
    print()

    print("Demo completed successfully.")
