# safe_httpeex

A re-implementation of the [httpeex](https://github.com/notactuallytreyanastasio/httpeex) HEEx template parser that replaces manual HTML escaping with Temper's compile-time safe HTML accumulator pattern. The tokenizer and parser are unchanged — only the renderer was replaced to make XSS prevention structural rather than manual.

## The Problem

The original httpeex renderer uses `StringBuilder` with manual `escapeHtml()` calls. This works for text content, but 6 code paths emit user content with **no escaping at all**:

```temper
// Original — StringBuilder, manual discipline
let renderExpression(expr: Expression, out: StringBuilder): Void {
  out.append("{");
  out.append(expr.code);     // unescaped — XSS vector
  out.append("}");
}

let renderComment(comment: Comment, out: StringBuilder): Void {
  out.append("<!-- ");
  out.append(comment.content);  // unescaped — XSS vector
  out.append(" -->");
}
```

Dynamic attributes, spread attributes, special attributes, and EEx code blocks all have the same gap. The escaping that does exist only covers 3 characters (`& < >`), missing `"` and `'` which enable attribute breakout attacks.

## The Fix

Replace `StringBuilder` with `SafeHtmlBuilder`. The type itself enforces the boundary:

- **`appendSafe(s)`** — for trusted template structure (tags, attribute names, delimiters)
- **`append(value)`** — for untrusted user content (auto-escapes all 5 OWASP characters)

```temper
// Safe — SafeHtmlBuilder, enforced by type
let renderExpression(expr: Expression, out: SafeHtmlBuilder): Void {
  out.appendSafe("{");
  out.append(expr.code);     // auto-escaped — safe
  out.appendSafe("}");
}

let renderComment(comment: Comment, out: SafeHtmlBuilder): Void {
  out.appendSafe("<!-- ");
  out.append(comment.content);  // auto-escaped — safe
  out.appendSafe(" -->");
}
```

The code looks almost the same. The difference is the type: calling `out.append()` on a `SafeHtmlBuilder` escapes; calling it on a `StringBuilder` doesn't.

## Escaping Coverage

| Character | Original httpeex | safe_httpeex |
|-----------|-----------------|-------------|
| `&` → `&amp;` | text only | everywhere |
| `<` → `&lt;` | text only | everywhere |
| `>` → `&gt;` | text only | everywhere |
| `"` → `&quot;` | attrs only | everywhere |
| `'` → `&#39;` | never | everywhere |

## What Changed

The tokenizer, parser, and AST are **identical** to the original httpeex. The diff is:

| File | Change |
|------|--------|
| `safe_html.temper.md` | **New** — SafeHtmlBuilder class + 5-char escape function (125 lines) |
| `renderer.temper.md` | **Rewritten** — `StringBuilder` → `SafeHtmlBuilder`, structure via `appendSafe()` |
| `exports.temper.md` | **Updated** — exports `SafeHtmlBuilder` for consumer tagged strings |
| `tokenizer.temper.md` | Unchanged |
| `parser.temper.md` | Unchanged |
| `ast.temper.md` | Unchanged |

## Tagged String API

Consumers can use `SafeHtmlBuilder` as a Temper tagged string for their own templates:

```temper
let userInput = "<script>alert('xss')</script>";
let html = SafeHtmlBuilder"<div class=\"container\">${userInput}</div>";
// Result: <div class="container">&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;</div>
```

The compiler routes literal parts to `appendSafe()` and `${expr}` interpolations to `append()` — no manual escaping required.

## Architecture

```
Template String
     │
     ▼
┌──────────┐
│ Tokenizer │  → List<Token>        (unchanged from httpeex)
└──────────┘
     │
     ▼
┌──────────┐
│  Parser   │  → Document AST       (unchanged from httpeex)
└──────────┘
     │
     ▼
┌──────────┐
│ Renderer  │  → Safe HTML String   (SafeHtmlBuilder instead of StringBuilder)
└──────────┘
```

## Build & Test

Requires the [Temper](https://github.com/nicholasgasior/temper) compiler.

```bash
temper build -b js     # JavaScript
temper build -b py     # Python
temper build -b lua    # Lua
```

Tests pass on JS, Python, and Lua backends (80/80 each):

```bash
temper test -b js
temper test -b py
temper test -b lua
```

## Test Coverage

80 tests covering:
- **Roundtrip fidelity** — parse → render → re-parse produces identical AST
- **XSS prevention** — script injection, attribute breakout, comment breakout all blocked
- **Character escaping** — all 5 characters verified individually, no double-escaping
- **Structure preservation** — tag names, static attributes, component syntax unchanged

## Python Example

```bash
PYTHONPATH=temper.out/py/safe-heex:temper.out/py/temper-core:temper.out/py/std \
  python3 examples/python_demo.py
```

```python
from safe_heex import parseTemplate, renderToHtml, SafeHtmlBuilder

doc = parseTemplate("<div>{@name}</div>")
html = renderToHtml(doc)
```

## Known Issues

- **Rust backend**: compile fails due to Temper compiler codegen bug with mutable variables in `when` blocks (not in our code)
- **C# backend**: Newline codegen bug in Temper compiler
- **Java backend**: untested (requires `mvn`)

## Comparison

See [COMPARISON_REPORT.md](COMPARISON_REPORT.md) for a detailed side-by-side analysis of safe_httpeex vs httpeex-accumulator vs the original httpeex.

## License

MIT
