# Safe HEEx Public API

This module defines the public API surface for the safe HEEx parser library.
It re-exports the core functions and types that consumers should use.

## Module Dependencies

This file uses types and functions from ast.temper.md, tokenizer.temper.md,
parser.temper.md, renderer.temper.md, and safe_html.temper.md.
All files in this directory are automatically combined into the "heex" module.

## Core Parsing Functions

The primary entry points for parsing HEEx templates.

### parse

Parse a HEEx template string into a Document AST.

```temper
export let parseTemplate(input: String): Document throws Bubble {
  parse(input)
}
```

### tokenize

Tokenize a HEEx template string into a list of tokens.
Useful for syntax highlighting or custom processing.

```temper
export let tokenizeTemplate(input: String): List<Token> throws Bubble {
  tokenize(input)
}
```

## Rendering Functions

Convert a Document AST back to various output formats.

### renderToHtml

Render the AST to a **safe** HTML string. Uses SafeHtmlBuilder internally —
template structure is trusted, user content is auto-escaped.

```temper
export let renderToHtml(doc: Document): String {
  renderHtml(doc)
}
```

### renderToDebug

Render the AST to a debug string showing the tree structure.
Useful for development and debugging.

```temper
export let renderToDebug(doc: Document): String {
  renderDebug(doc)
}
```

### renderToJson

Serialize the AST to JSON format for tooling integration.

```temper
export let renderToJson(doc: Document): String {
  renderJson(doc)
}
```

## Convenience Functions

Combined operations for common use cases.

### parseAndRender

Parse a template and immediately render it back to safe HTML.
Useful for validating templates or normalizing whitespace.

```temper
export let parseAndRender(input: String): String throws Bubble {
  let doc = parse(input);
  renderHtml(doc)
}
```

### parseAndValidate

Parse a template and return true if valid, throws Bubble with errors if not.

```temper
export let parseAndValidate(input: String): Boolean throws Bubble {
  parse(input);
  true
}
```

## SafeHtmlBuilder Export

Export the SafeHtmlBuilder type for direct use as a tagged string tag.
Consumers can write safe HTML templates directly:

```
let html = SafeHtml"<div class=\"container\">${userContent}</div>";
```

The compiler routes literal parts to `appendSafe` (trusted) and
`${expr}` interpolations to `append` (auto-escaped).

```temper
export let safeHtml = SafeHtmlBuilder;
```

## Error Handling

All parsing functions throw `Bubble` on error. The error message contains
all parse errors with line and column information.

Example usage:

```
// In consuming code (pseudocode):
// let doc = parseTemplate("<div>{@name}</div>") orelse bubble();
// let html = renderToHtml(doc);
// console.log(html);
```

## Version Information

```temper
export let VERSION = "0.1.0";
export let NAME = "safe-heex";
```
