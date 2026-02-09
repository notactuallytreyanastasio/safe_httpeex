# Tokenizer Tests

Unit tests for the HEEx tokenizer.

## Setup

All symbols are imported via imports.temper.md from the parent heex module.

## Text Tokenization

```temper
test("tokenizes plain text") {
  let tokens = tokenize("Hello world");
  assert(tokens.length >= 1);
  assert(tokens[0].tokenType.kind == "text");
  assert(tokens[0].value == "Hello world");
}

test("tokenizes whitespace") {
  let tokens = tokenize("   ");
  assert(tokens.length >= 1);
}
```

## Tag Tokenization

```temper
test("tokenizes opening tag") {
  let tokens = tokenize("<div>");
  assert(tokens.length >= 2);
}

test("tokenizes closing tag") {
  let tokens = tokenize("</div>");
  assert(tokens.length >= 1);
}

test("tokenizes self-closing tag") {
  let tokens = tokenize("<br/>");
  assert(tokens.length >= 1);
}
```

## Attribute Tokenization

```temper
test("tokenizes attribute") {
  let tokens = tokenize("<div class=\"foo\">");
  assert(tokens.length >= 4);
}

test("tokenizes multiple attributes") {
  let tokens = tokenize("<div id=\"main\" class=\"container\">");
  assert(tokens.length >= 6);
}
```

## Expression Tokenization

```temper
test("tokenizes expression") {
  let tokens = tokenize("{@value}");
  assert(tokens.length >= 3);
}

test("tokenizes dynamic attribute") {
  let tokens = tokenize("<div class={@class}>");
  assert(tokens.length >= 5);
}
```

## EEx Tokenization

```temper
test("tokenizes eex output") {
  let tokens = tokenize("<%= @name %>");
  assert(tokens.length >= 3);
}

test("tokenizes eex eval") {
  let tokens = tokenize("<% code %>");
  assert(tokens.length >= 3);
}

test("tokenizes eex comment") {
  let tokens = tokenize("<%# comment %>");
  assert(tokens.length >= 3);
}
```

## Component Tokenization

```temper
test("tokenizes local component") {
  let tokens = tokenize("<.button>");
  assert(tokens.length >= 2);
}

test("tokenizes remote component") {
  let tokens = tokenize("<MyApp.Button>");
  assert(tokens.length >= 2);
}
```

## Slot Tokenization

```temper
test("tokenizes slot open") {
  let tokens = tokenize("<:header>");
  assert(tokens.length >= 2);
}

test("tokenizes slot close") {
  let tokens = tokenize("</:header>");
  assert(tokens.length >= 1);
}
```

## Comment Tokenization

```temper
test("tokenizes HTML comment") {
  let tokens = tokenize("<!-- comment -->");
  assert(tokens.length >= 1);
}
```
