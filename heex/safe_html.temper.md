# Safe HTML Builder

This module defines the `SafeHtmlBuilder` accumulator type — the core contribution
of safe_httpeex. It provides **compile-time XSS prevention** by separating trusted
HTML structure from untrusted user content at the type level.

## How It Works

The builder implements Temper's **tagged string accumulator pattern**:

- **`appendSafe(s)`** — Appends trusted HTML literals verbatim (template structure)
- **`append(value)`** — Appends untrusted content after HTML-escaping (user data)
- **`accumulated`** — Returns the final safe HTML string

When used as a tagged string, the Temper compiler automatically routes literal
string parts to `appendSafe` and `${expr}` interpolations to `append`:

```text
SafeHtml"<div>${userContent}</div>"
```

desugars to:

```text
let acc = new SafeHtmlBuilder();
acc.appendSafe("<div>");
acc.append(userContent);    // HTML-escaped automatically
acc.appendSafe("</div>");
acc.accumulated
```

## Character Constants for Escaping

```temper
class EscapeChars {
  public static let AMP: Int = char'&';
  public static let LT: Int = char'<';
  public static let GT: Int = char'>';
  public static let DQUOTE: Int = char'"';
  public static let SQUOTE: Int = char'\'';
}
```

## HTML Escaping

Escapes the five critical HTML characters to prevent injection.

```temper
let escapeHtml(s: String): String {
  let out = new StringBuilder();
  var idx = String.begin;
  while (s.hasIndex(idx)) {
    let c = s[idx];
    if (c == EscapeChars.AMP) {
      out.append("&amp;");
    } else if (c == EscapeChars.LT) {
      out.append("&lt;");
    } else if (c == EscapeChars.GT) {
      out.append("&gt;");
    } else if (c == EscapeChars.DQUOTE) {
      out.append("&quot;");
    } else if (c == EscapeChars.SQUOTE) {
      out.append("&#39;");
    } else {
      out.appendCodePoint(c) orelse void;
    }
    idx = s.next(idx);
  }
  out.toString()
}
```

## Attribute Value Escaping

Same as HTML escaping — attribute contexts need the same characters escaped.

```temper
let escapeAttr(s: String): String {
  escapeHtml(s)
}
```

## The SafeHtmlBuilder Class

The accumulator that makes HTML safe by construction. Implements the three
methods required by Temper's tagged string system.

```temper
export class SafeHtmlBuilder {
  private var parts: ListBuilder<String>;

  public constructor() {
    parts = new ListBuilder<String>();
  }

  // Trusted literal HTML — appended verbatim, no escaping.
  // Called by the compiler for string literal parts in tagged strings.
  public appendSafe(s: String): Void {
    parts.add(s);
  }

  // Untrusted user content — HTML-escaped before appending.
  // Called by the compiler for ${expr} interpolations in tagged strings.
  public append(value: String): Void {
    parts.add(escapeHtml(value));
  }

  // Returns the final safe HTML string.
  public get accumulated(): String {
    let result = new StringBuilder();
    for (let part of parts.toList()) {
      result.append(part);
    }
    result.toString()
  }
}
```

## Convenience Export

Export the type so consumers can use it as a tagged string tag.

```temper
export let SafeHtml = SafeHtmlBuilder;
```
