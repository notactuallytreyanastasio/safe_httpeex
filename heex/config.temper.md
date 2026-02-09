# Safe HEEx Parser for Temper

A cross-platform implementation of Phoenix LiveView's HEEx templating language
with **compile-time XSS prevention** via Temper's safe HTML accumulator pattern.

This is a re-implementation of [httpeex](../httpeex) using Temper's tagged string
features for type-safe HTML output.

## Package Metadata

```temper
export let name = "safe-heex";
export let version = "0.1.0";
export let description = "Safe HEEx template parser and renderer with compile-time XSS prevention";
export let license = "MIT";
export let authors = ["safe_httpeex contributors"];
```

## Backend-Specific Configuration

```temper
export let javaGroup = "dev.httpeex";
export let javaName = "safe-heex-java";
export let jsName = "@httpeex/safe-heex";
export let pyName = "safe-heex-py";
export let rustName = "safe-heex-rs";
```

## Imports

Import the main module.

```temper
import(".");
import("./tests");
```

## Module Structure

The library is organized into focused files that are all part of the "heex" module:

- **safe_html.temper.md** - SafeHtmlBuilder accumulator (the core safe templating type)
- **ast.temper.md** - Core AST definitions (data structures representing parsed templates)
- **tokenizer.temper.md** - Lexical analysis (converts text to tokens)
- **parser.temper.md** - Syntax analysis (converts tokens to AST)
- **renderer.temper.md** - Output generation using SafeHtmlBuilder for HTML
- **exports.temper.md** - Public API surface

All files in this directory are automatically combined into a single Temper module.

## Design Philosophy

### Safe by Construction

The key innovation: HTML rendering uses `SafeHtmlBuilder` instead of `StringBuilder`.
The accumulator pattern separates trusted HTML structure (`appendSafe`) from
untrusted user content (`append`, which auto-escapes). This makes XSS
**impossible by construction** rather than by runtime escaping discipline.

### Tagged String Integration

`SafeHtmlBuilder` can be used as a Temper tagged string tag:
```text
SafeHtml"<div>${userContent}</div>"
```
The compiler routes literal parts to `appendSafe` and `${expr}` to `append`.

### Three-Stage Pipeline

Following HEEx's original architecture:
1. **Tokenization**: Raw template → Token stream
2. **Parsing**: Token stream → Abstract Syntax Tree
3. **Safe Rendering**: AST → Safe HTML output

### Error-Tolerant Processing

Like the `temper-regex-parser`, we collect errors rather than failing fast.
This provides better developer experience with multiple error reports.
