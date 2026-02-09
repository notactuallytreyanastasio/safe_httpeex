# HEEx Abstract Syntax Tree

This module defines the data structures representing parsed HEEx templates.
The AST is designed to be platform-agnostic and suitable for multiple outputs.

## Core Concepts

HEEx templates contain:
- **HTML elements** with static and dynamic attributes
- **Components** (local and remote function calls)
- **Slots** for content composition
- **Expressions** for interpolation
- **EEx blocks** for control flow

## Node Interface

All AST nodes implement a common interface for traversal and rendering.

```temper
export interface Node {
  // Get the type name for pattern matching
  nodeType(): String;

  // Convert to a debug string representation
  toString(): String;
}
```

## Source Location

Track positions for error reporting and tooling integration.

```temper
export class Location(
  public line: Int,
  public column: Int,
  public offset: Int,
) {
  public toString(): String {
    "${line}:${column}"
  }
}

export class Span(
  public start: Location,
  public end: Location,
) {
  public toString(): String {
    "${start}-${end}"
  }
}
```

## Document Root

The top-level container for a parsed template.

```temper
export class Document(
  public children: List<Node>,
  public span: Span?,
) extends Node {
  public nodeType(): String { "document" }

  public toString(): String {
    "Document(${children.length} children)"
  }
}
```

## Text Content

Static text that appears between tags or expressions.

```temper
export class Text(
  public content: String,
  public span: Span?,
) extends Node {
  public nodeType(): String { "text" }

  public toString(): String {
    "Text(\"${content}\")"
  }
}
```

## HTML Elements

Standard HTML tags with attributes and children.

```temper
export class Element(
  public tag: String,
  public attributes: List<Attribute>,
  public children: List<Node>,
  public selfClosing: Boolean,
  public span: Span?,
) extends Node {
  public nodeType(): String { "element" }

  public toString(): String {
    "<${tag}>"
  }
}
```

## Attributes

Attributes can be static strings, dynamic expressions, or spreads.

```temper
export interface Attribute {
  attributeType(): String;
}

// Static attribute: name="value"
export class StaticAttribute(
  public name: String,
  public value: String,
  public span: Span?,
) extends Attribute {
  public attributeType(): String { "static" }
}

// Dynamic attribute: name={expression}
export class DynamicAttribute(
  public name: String,
  public expression: Expression,
  public span: Span?,
) extends Attribute {
  public attributeType(): String { "dynamic" }
}

// Spread attribute: {@attrs}
export class SpreadAttribute(
  public expression: Expression,
  public span: Span?,
) extends Attribute {
  public attributeType(): String { "spread" }
}

// Special attribute: :if, :for, :key
export class SpecialAttribute(
  public kind: String,  // "if", "for", "key"
  public expression: Expression,
  public span: Span?,
) extends Attribute {
  public attributeType(): String { "special" }
}
```

## Expressions

Dynamic content that will be evaluated at runtime.

```temper
export class Expression(
  public code: String,      // The raw expression text
  public span: Span?,
) extends Node {
  public nodeType(): String { "expression" }

  public toString(): String {
    "Expression(${code})"
  }
}
```

## Components

Components are function calls that render content.

```temper
// Component type: local (.name) or remote (Module.name)
export class ComponentType {
  public static let Local = new ComponentType("local");
  public static let Remote = new ComponentType("remote");

  public var kind: String;

  public constructor(k: String) {
    kind = k;
  }
}

export class Component(
  public componentType: ComponentType,
  public name: String,              // "button" or "MyApp.Button"
  public attributes: List<Attribute>,
  public children: List<Node>,      // Default slot content
  public slots: List<Slot>,         // Named slots
  public span: Span?,
) extends Node {
  public nodeType(): String { "component" }

  public toString(): String {
    if (componentType.kind == "local") {
      "<.${name}>"
    } else {
      "<${name}>"
    }
  }
}
```

## Slots

Named content regions within components.

```temper
export class Slot(
  public name: String,              // Slot name (e.g., "header", "footer")
  public attributes: List<Attribute>,
  public children: List<Node>,
  public letBinding: String?,       // :let={var} binding name
  public span: Span?,
) extends Node {
  public nodeType(): String { "slot" }

  public toString(): String {
    "<:${name}>"
  }
}
```

## EEx Blocks

Embedded Elixir expressions and control flow.

```temper
// EEx expression type
export class EExType {
  public static let Output = new EExType("output");     // <%= ... %>
  public static let Exec = new EExType("exec");         // <% ... %>
  public static let Comment = new EExType("comment");   // <%# ... %>

  public var kind: String;

  public constructor(k: String) {
    kind = k;
  }
}

export class EEx(
  public eexType: EExType,
  public code: String,
  public span: Span?,
) extends Node {
  public nodeType(): String { "eex" }

  public toString(): String {
    if (eexType.kind == "output") {
      "<%= ${code} %>"
    } else if (eexType.kind == "comment") {
      "<%# ${code} %>"
    } else {
      "<% ${code} %>"
    }
  }
}
```

## EEx Block Structures

Control flow blocks like `if/else`, `case`, `for`.

```temper
export class EExBlock(
  public blockType: String,         // "if", "case", "for", etc.
  public expression: String,        // The condition/iterator expression
  public clauses: List<EExClause>,  // Block clauses (do, else, end)
  public span: Span?,
) extends Node {
  public nodeType(): String { "eex_block" }

  public toString(): String {
    "<%= ${blockType} ${expression} do %>"
  }
}

export class EExClause(
  public clauseType: String,        // "do", "else", "end", "->", etc.
  public expression: String?,       // For case clauses
  public children: List<Node>,
  public span: Span?,
) {
  public toString(): String {
    "<% ${clauseType} %>"
  }
}
```

## HTML Comments

```temper
export class Comment(
  public content: String,
  public span: Span?,
) extends Node {
  public nodeType(): String { "comment" }

  public toString(): String {
    "<!-- ${content} -->"
  }
}
```

## Utility Functions

Helper functions for working with the AST.

```temper
// Check if a tag is a void element (self-closing in HTML5)
export let voidElements = [
  "area", "base", "br", "col", "embed", "hr", "img", "input",
  "link", "meta", "param", "source", "track", "wbr"
];

// Helper to check if list contains a string (case-insensitive for void elements)
let listContainsIgnoreCase(list: List<String>, item: String): Boolean {
  for (let elem of list) {
    // Simple lowercase comparison for ASCII tags
    if (elem == item) {
      return true;
    }
  }
  false
}

export let isVoidElement(tag: String): Boolean {
  // Void element tags are all lowercase in HTML5
  listContainsIgnoreCase(voidElements, tag)
}

// Helper to check if string starts with a character
let startsWithChar(s: String, c: Int): Boolean {
  if (s.hasIndex(String.begin)) {
    s[String.begin] == c
  } else {
    false
  }
}

// Check if a name indicates a local component (starts with .)
export let isLocalComponent(name: String): Boolean {
  startsWithChar(name, char'.')
}

// Check if a name indicates a remote component (starts with uppercase A-Z)
export let isRemoteComponent(name: String): Boolean {
  if (!name.hasIndex(String.begin)) {
    return false;
  }
  let first = name[String.begin];
  first >= char'A' && first <= char'Z'
}

// Check if a name indicates a slot (starts with :)
export let isSlot(name: String): Boolean {
  startsWithChar(name, char':')
}
```
