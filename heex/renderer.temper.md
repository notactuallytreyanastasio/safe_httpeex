# HEEx Safe Renderer

The renderer converts an AST back into various output formats.
This is the third stage of the pipeline and the **key difference** from the
original httpeex — HTML rendering uses `SafeHtmlBuilder` instead of `StringBuilder`.

## Overview

The renderer supports multiple output modes:

1. **Safe HTML String** — Uses `SafeHtmlBuilder` for XSS prevention by construction
2. **Debug String** — AST visualization for development (plain StringBuilder)
3. **JSON** — Serialized AST for tooling integration (plain StringBuilder)

## Module Dependencies

This file uses types from ast.temper.md and SafeHtmlBuilder from safe_html.temper.md.
All files in this directory are automatically combined into the "heex" module.

## Character Constants for Rendering

```temper
class RenderChars {
  public static let AMP: Int = char'&';
  public static let LT: Int = char'<';
  public static let GT: Int = char'>';
  public static let DQUOTE: Int = char'"';
  public static let BACKSLASH: Int = char'\\';
  public static let NEWLINE: Int = char'\n';
  public static let CR: Int = char'\r';
  public static let TAB: Int = char'\t';
}
```

## Safe HTML Rendering

Render the AST to a safe HTML string using the SafeHtmlBuilder accumulator.
Template structure (tags, attribute names, static values) goes through `appendSafe`.
User content (expressions, dynamic values, text) goes through `append` (auto-escaped).

```temper
export let renderHtml(doc: Document): String {
  let out = new SafeHtmlBuilder();
  for (let child of doc.children) {
    renderNode(child, out);
  }
  out.accumulated
}

let renderNode(node: Node, out: SafeHtmlBuilder): Void {
  when (node) {
    is Text -> out.append(node.content);
    is Element -> renderElement(node, out);
    is Component -> renderComponent(node, out);
    is Slot -> renderSlot(node, out);
    is Expression -> renderExpression(node, out);
    is EEx -> renderEEx(node, out);
    is EExBlock -> renderEExBlock(node, out);
    is Comment -> renderComment(node, out);
    else -> void;
  }
}
```

## Element Rendering

Tag names and HTML syntax are trusted (appendSafe). Children are rendered recursively.

```temper
let renderElement(el: Element, out: SafeHtmlBuilder): Void {
  out.appendSafe("<");
  out.appendSafe(el.tag);

  // Render attributes
  renderAttributes(el.attributes, out);

  // Self-closing or void element
  if (el.selfClosing || isVoidElement(el.tag)) {
    out.appendSafe(" />");
    return;
  }

  out.appendSafe(">");

  // Render children
  for (let child of el.children) {
    renderNode(child, out);
  }

  out.appendSafe("</");
  out.appendSafe(el.tag);
  out.appendSafe(">");
}
```

## Component Rendering

Component names come from template source — trusted via appendSafe.

```temper
let renderComponent(comp: Component, out: SafeHtmlBuilder): Void {
  out.appendSafe("<");
  out.appendSafe(comp.name);

  // Render attributes
  renderAttributes(comp.attributes, out);

  // No children or slots - self-close
  if (comp.children.length == 0 && comp.slots.length == 0) {
    out.appendSafe(" />");
    return;
  }

  out.appendSafe(">");

  // Render default slot children
  for (let child of comp.children) {
    renderNode(child, out);
  }

  // Render named slots
  for (let slot of comp.slots) {
    renderSlot(slot, out);
  }

  out.appendSafe("</");
  out.appendSafe(comp.name);
  out.appendSafe(">");
}
```

## Slot Rendering

Slot syntax is template structure — trusted.

```temper
let renderSlot(slot: Slot, out: SafeHtmlBuilder): Void {
  out.appendSafe("<:");
  out.appendSafe(slot.name);

  // Render attributes
  renderAttributes(slot.attributes, out);

  if (slot.children.length == 0) {
    out.appendSafe(" />");
    return;
  }

  out.appendSafe(">");

  for (let child of slot.children) {
    renderNode(child, out);
  }

  out.appendSafe("</:");
  out.appendSafe(slot.name);
  out.appendSafe(">");
}
```

## Attribute Rendering

Attribute names are trusted (from template source).
Static attribute values are trusted (written by template author).
Dynamic expressions are untrusted (user data — auto-escaped via append).

```temper
let renderAttributes(attrs: List<Attribute>, out: SafeHtmlBuilder): Void {
  for (let attr of attrs) {
    out.appendSafe(" ");
    when (attr) {
      is StaticAttribute -> do {
        out.appendSafe(attr.name);
        out.appendSafe("=\"");
        out.appendSafe(attr.value);
        out.appendSafe("\"");
      };
      is DynamicAttribute -> do {
        out.appendSafe(attr.name);
        out.appendSafe("={");
        out.append(attr.expression.code);
        out.appendSafe("}");
      };
      is SpreadAttribute -> do {
        out.appendSafe("{");
        out.append(attr.expression.code);
        out.appendSafe("}");
      };
      is SpecialAttribute -> do {
        out.appendSafe(":");
        out.appendSafe(attr.kind);
        out.appendSafe("={");
        out.append(attr.expression.code);
        out.appendSafe("}");
      };
      else -> void;
    }
  }
}
```

## Expression Rendering

Expression delimiters are trusted. Expression content is untrusted (auto-escaped).

```temper
let renderExpression(expr: Expression, out: SafeHtmlBuilder): Void {
  out.appendSafe("{");
  out.append(expr.code);
  out.appendSafe("}");
}
```

## EEx Rendering

EEx delimiters and block keywords are trusted template structure.
EEx code content is untrusted (auto-escaped).

```temper
let renderEEx(eex: EEx, out: SafeHtmlBuilder): Void {
  let kind = eex.eexType.kind;
  if (kind == "output") {
    out.appendSafe("<%= ");
    out.append(eex.code);
    out.appendSafe(" %>");
  } else if (kind == "comment") {
    out.appendSafe("<%# ");
    out.append(eex.code);
    out.appendSafe(" %>");
  } else {
    out.appendSafe("<% ");
    out.append(eex.code);
    out.appendSafe(" %>");
  }
}

let renderEExBlock(block: EExBlock, out: SafeHtmlBuilder): Void {
  out.appendSafe("<%= ");
  out.appendSafe(block.blockType);
  out.appendSafe(" ");
  out.append(block.expression);
  out.appendSafe(" do %>");

  for (let clause of block.clauses) {
    let ctype = clause.clauseType;
    if (ctype == "do") {
      for (let child of clause.children) {
        renderNode(child, out);
      }
    } else if (ctype == "else") {
      out.appendSafe("<% else %>");
      for (let child of clause.children) {
        renderNode(child, out);
      }
    } else if (ctype == "end") {
      out.appendSafe("<% end %>");
    } else {
      out.appendSafe("<% ");
      let expr = clause.expression;
      when (expr) {
        is String -> out.append(expr);
        else -> void;
      }
      out.appendSafe(" %>");
      for (let child of clause.children) {
        renderNode(child, out);
      }
    }
  }
}
```

## Comment Rendering

Comment delimiters are trusted. Comment content passes through append (auto-escaped).

```temper
let renderComment(comment: Comment, out: SafeHtmlBuilder): Void {
  out.appendSafe("<!-- ");
  out.append(comment.content);
  out.appendSafe(" -->");
}
```

## Debug Output

Debug rendering uses plain StringBuilder — it's for developer use, not user-facing HTML.

```temper
export let renderDebug(doc: Document): String {
  let out = new StringBuilder();
  out.append("Document\n");
  for (let child of doc.children) {
    renderDebugNode(child, out, "  ");
  }
  out.toString()
}

let renderDebugNode(node: Node, out: StringBuilder, indent: String): Void {
  out.append(indent);

  when (node) {
    is Text -> do {
      out.append("Text: \"");
      out.append(escapeNewlines(node.content));
      out.append("\"\n");
    };
    is Element -> do {
      out.append("Element: <");
      out.append(node.tag);
      out.append(">\n");
      for (let attr of node.attributes) {
        renderDebugAttr(attr, out, "${indent}  ");
      }
      for (let child of node.children) {
        renderDebugNode(child, out, "${indent}  ");
      }
    };
    is Component -> do {
      out.append("Component: ");
      out.append(node.name);
      out.append("\n");
      for (let attr of node.attributes) {
        renderDebugAttr(attr, out, "${indent}  ");
      }
      for (let child of node.children) {
        renderDebugNode(child, out, "${indent}  ");
      }
      for (let slot of node.slots) {
        renderDebugNode(slot, out, "${indent}  ");
      }
    };
    is Slot -> do {
      out.append("Slot: <:");
      out.append(node.name);
      out.append(">\n");
      for (let child of node.children) {
        renderDebugNode(child, out, "${indent}  ");
      }
    };
    is Expression -> do {
      out.append("Expression: {");
      out.append(node.code);
      out.append("}\n");
    };
    is EEx -> do {
      out.append("EEx: ");
      out.append(node.eexType.kind);
      out.append(" \"");
      out.append(node.code);
      out.append("\"\n");
    };
    is EExBlock -> do {
      out.append("EExBlock: ");
      out.append(node.blockType);
      out.append(" ");
      out.append(node.expression);
      out.append("\n");
      for (let clause of node.clauses) {
        out.append("${indent}  Clause: ");
        out.append(clause.clauseType);
        out.append("\n");
        for (let child of clause.children) {
          renderDebugNode(child, out, "${indent}    ");
        }
      }
    };
    is Comment -> do {
      out.append("Comment: ");
      out.append(node.content);
      out.append("\n");
    };
    else -> do {
      out.append("Unknown node\n");
    };
  }
}

// Escape newlines for debug output
let escapeNewlines(s: String): String {
  let out = new StringBuilder();
  var idx = String.begin;
  while (s.hasIndex(idx)) {
    let c = s[idx];
    if (c == RenderChars.NEWLINE) {
      out.append("\\n");
    } else if (c == RenderChars.CR) {
      out.append("\\r");
    } else if (c == RenderChars.TAB) {
      out.append("\\t");
    } else {
      out.appendCodePoint(c) orelse void;
    }
    idx = s.next(idx);
  }
  out.toString()
}

let renderDebugAttr(attr: Attribute, out: StringBuilder, indent: String): Void {
  out.append(indent);
  out.append("Attr: ");
  when (attr) {
    is StaticAttribute -> do {
      out.append(attr.name);
      out.append("=\"");
      out.append(attr.value);
      out.append("\"");
    };
    is DynamicAttribute -> do {
      out.append(attr.name);
      out.append("={");
      out.append(attr.expression.code);
      out.append("}");
    };
    is SpreadAttribute -> do {
      out.append("{");
      out.append(attr.expression.code);
      out.append("}");
    };
    is SpecialAttribute -> do {
      out.append(":");
      out.append(attr.kind);
      out.append("={");
      out.append(attr.expression.code);
      out.append("}");
    };
    else -> void;
  }
  out.append("\n");
}
```

## JSON Serialization

JSON rendering uses plain StringBuilder — it's for tooling, not user-facing HTML.

```temper
export let renderJson(doc: Document): String {
  let out = new StringBuilder();
  out.append("{\"type\":\"document\",\"children\":[");
  var first = true;
  for (let child of doc.children) {
    if (!first) {
      out.append(",");
    }
    first = false;
    renderJsonNode(child, out);
  }
  out.append("]}");
  out.toString()
}

let renderJsonNode(node: Node, out: StringBuilder): Void {
  when (node) {
    is Text -> do {
      out.append("{\"type\":\"text\",\"content\":");
      jsonString(node.content, out);
      out.append("}");
    };
    is Element -> do {
      out.append("{\"type\":\"element\",\"tag\":");
      jsonString(node.tag, out);
      out.append(",\"attributes\":[");
      var first = true;
      for (let attr of node.attributes) {
        if (!first) { out.append(","); }
        first = false;
        renderJsonAttr(attr, out);
      }
      out.append("],\"children\":[");
      first = true;
      for (let child of node.children) {
        if (!first) { out.append(","); }
        first = false;
        renderJsonNode(child, out);
      }
      out.append("]}");
    };
    is Component -> do {
      out.append("{\"type\":\"component\",\"name\":");
      jsonString(node.name, out);
      out.append(",\"componentType\":\"");
      out.append(node.componentType.kind);
      out.append("\",\"attributes\":[");
      var first = true;
      for (let attr of node.attributes) {
        if (!first) { out.append(","); }
        first = false;
        renderJsonAttr(attr, out);
      }
      out.append("],\"children\":[");
      first = true;
      for (let child of node.children) {
        if (!first) { out.append(","); }
        first = false;
        renderJsonNode(child, out);
      }
      out.append("],\"slots\":[");
      first = true;
      for (let slot of node.slots) {
        if (!first) { out.append(","); }
        first = false;
        renderJsonNode(slot, out);
      }
      out.append("]}");
    };
    is Slot -> do {
      out.append("{\"type\":\"slot\",\"name\":");
      jsonString(node.name, out);
      out.append(",\"children\":[");
      var first = true;
      for (let child of node.children) {
        if (!first) { out.append(","); }
        first = false;
        renderJsonNode(child, out);
      }
      out.append("]}");
    };
    is Expression -> do {
      out.append("{\"type\":\"expression\",\"code\":");
      jsonString(node.code, out);
      out.append("}");
    };
    is EEx -> do {
      out.append("{\"type\":\"eex\",\"eexType\":\"");
      out.append(node.eexType.kind);
      out.append("\",\"code\":");
      jsonString(node.code, out);
      out.append("}");
    };
    is Comment -> do {
      out.append("{\"type\":\"comment\",\"content\":");
      jsonString(node.content, out);
      out.append("}");
    };
    else -> out.append("null");
  }
}

let renderJsonAttr(attr: Attribute, out: StringBuilder): Void {
  when (attr) {
    is StaticAttribute -> do {
      out.append("{\"type\":\"static\",\"name\":");
      jsonString(attr.name, out);
      out.append(",\"value\":");
      jsonString(attr.value, out);
      out.append("}");
    };
    is DynamicAttribute -> do {
      out.append("{\"type\":\"dynamic\",\"name\":");
      jsonString(attr.name, out);
      out.append(",\"expression\":");
      jsonString(attr.expression.code, out);
      out.append("}");
    };
    is SpreadAttribute -> do {
      out.append("{\"type\":\"spread\",\"expression\":");
      jsonString(attr.expression.code, out);
      out.append("}");
    };
    is SpecialAttribute -> do {
      out.append("{\"type\":\"special\",\"kind\":");
      jsonString(attr.kind, out);
      out.append(",\"expression\":");
      jsonString(attr.expression.code, out);
      out.append("}");
    };
    else -> out.append("null");
  }
}

let jsonString(s: String, out: StringBuilder): Void {
  out.append("\"");
  var idx = String.begin;
  while (s.hasIndex(idx)) {
    let c = s[idx];
    if (c == RenderChars.DQUOTE) {
      out.append("\\\"");
    } else if (c == RenderChars.BACKSLASH) {
      out.append("\\\\");
    } else if (c == RenderChars.NEWLINE) {
      out.append("\\n");
    } else if (c == RenderChars.CR) {
      out.append("\\r");
    } else if (c == RenderChars.TAB) {
      out.append("\\t");
    } else {
      out.appendCodePoint(c) orelse void;
    }
    idx = s.next(idx);
  }
  out.append("\"");
}
```
