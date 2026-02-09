# HEEx Tokenizer

The tokenizer converts raw template text into a stream of tokens.
This is the first stage of the parsing pipeline.

## Token Types

HEEx has several distinct token types representing different syntactic elements.

```temper
// This file uses Location, Span, and isRemoteComponent from ast.temper.md
// All files in this directory are automatically combined into the "heex" module.

// All possible token types in HEEx
export class TokenType {
  // Structural
  public static let Text = new TokenType("text");
  public static let Whitespace = new TokenType("whitespace");

  // Tags
  public static let TagOpen = new TokenType("tag_open");         // <div
  public static let TagClose = new TokenType("tag_close");       // </div>
  public static let TagSelfClose = new TokenType("tag_self_close"); // />
  public static let TagEnd = new TokenType("tag_end");           // >

  // Components
  public static let ComponentOpen = new TokenType("component_open");   // <.name or <Module.name
  public static let ComponentClose = new TokenType("component_close"); // </.name> or </Module.name>

  // Slots
  public static let SlotOpen = new TokenType("slot_open");       // <:name
  public static let SlotClose = new TokenType("slot_close");     // </:name>

  // Attributes
  public static let AttrName = new TokenType("attr_name");
  public static let AttrEquals = new TokenType("attr_equals");   // =
  public static let AttrValue = new TokenType("attr_value");     // "value" or 'value'

  // Expressions
  public static let ExprOpen = new TokenType("expr_open");       // {
  public static let ExprClose = new TokenType("expr_close");     // }
  public static let ExprContent = new TokenType("expr_content"); // content inside {}

  // EEx
  public static let EExOpen = new TokenType("eex_open");         // <%
  public static let EExOutput = new TokenType("eex_output");     // <%=
  public static let EExComment = new TokenType("eex_comment");   // <%#
  public static let EExClose = new TokenType("eex_close");       // %>
  public static let EExContent = new TokenType("eex_content");   // content inside <% %>

  // HTML Comments
  public static let CommentOpen = new TokenType("comment_open"); // <!--
  public static let CommentClose = new TokenType("comment_close"); // -->
  public static let CommentContent = new TokenType("comment_content");

  // Special
  public static let EOF = new TokenType("eof");

  public var kind: String;

  public constructor(k: String) {
    kind = k;
  }

  public toString(): String {
    kind
  }
}
```

## Token Structure

Each token carries its type, value, and source location.

```temper
export class Token(
  public tokenType: TokenType,
  public value: String,
  public span: Span,
) {
  public toString(): String {
    "${tokenType.kind}(\"${value}\")"
  }
}
```

## Character Constants

Define character code points for efficient comparison.

```temper
class Chars {
  public static let LT: Int = char'<';
  public static let GT: Int = char'>';
  public static let SLASH: Int = char'/';
  public static let COLON: Int = char':';
  public static let DOT: Int = char'.';
  public static let LBRACE: Int = char'{';
  public static let RBRACE: Int = char'}';
  public static let PERCENT: Int = char'%';
  public static let EQUALS: Int = char'=';
  public static let HASH: Int = char'#';
  public static let DQUOTE: Int = char'"';
  public static let SQUOTE: Int = char'\'';
  public static let BACKSLASH: Int = char'\\';
  public static let DASH: Int = char'-';
  public static let UNDERSCORE: Int = char'_';
  public static let NEWLINE: Int = char'\n';
  public static let TAB: Int = char'\t';
  public static let CR: Int = char'\r';
  public static let SPACE: Int = char' ';
  public static let BANG: Int = char'!';
  public static let LOWER_A: Int = char'a';
  public static let LOWER_Z: Int = char'z';
  public static let UPPER_A: Int = char'A';
  public static let UPPER_Z: Int = char'Z';
  public static let DIGIT_0: Int = char'0';
  public static let DIGIT_9: Int = char'9';
}
```

## Character Classification

Helper functions for classifying character code points.

```temper
export let isWhitespace(c: Int): Boolean {
  c == Chars.SPACE || c == Chars.TAB || c == Chars.NEWLINE || c == Chars.CR
}

export let isAlpha(c: Int): Boolean {
  (c >= Chars.LOWER_A && c <= Chars.LOWER_Z) || (c >= Chars.UPPER_A && c <= Chars.UPPER_Z)
}

export let isUpper(c: Int): Boolean {
  c >= Chars.UPPER_A && c <= Chars.UPPER_Z
}

export let isDigit(c: Int): Boolean {
  c >= Chars.DIGIT_0 && c <= Chars.DIGIT_9
}

export let isAlphaNumeric(c: Int): Boolean {
  isAlpha(c) || isDigit(c)
}

export let isNameChar(c: Int): Boolean {
  isAlphaNumeric(c) || c == Chars.UNDERSCORE || c == Chars.DASH || c == Chars.DOT
}

export let isNameStart(c: Int): Boolean {
  isAlpha(c) || c == Chars.UNDERSCORE
}
```

## Tokenizer State

The tokenizer maintains state as it processes the input.

```temper
export class Tokenizer(
  public chars: String,
  public var pos: StringIndex,
  public var line: Int,
  public var column: Int,
) {
  // Error collection for non-fatal errors
  public var errors: ListBuilder<String> = new ListBuilder<String>();

  // Token output
  public var tokens: ListBuilder<Token> = new ListBuilder<Token>();

  // Constructor with defaults
  public constructor(input: String) {
    chars = input;
    pos = String.begin;
    line = 1;
    column = 1;
    errors = new ListBuilder<String>();
    tokens = new ListBuilder<Token>();
  }

  // Check if we've consumed all input
  public isDone(): Boolean {
    !chars.hasIndex(pos)
  }

  // Peek at current character code point without consuming
  public peek(): Int? {
    if (isDone()) {
      null
    } else {
      chars[pos]
    }
  }

  // Peek ahead by n characters
  public peekAhead(n: Int): Int? {
    var idx = pos;
    for (var i = 0; i < n; i += 1) {
      if (!chars.hasIndex(idx)) {
        return null;
      }
      idx = chars.next(idx);
    }
    if (chars.hasIndex(idx)) {
      chars[idx]
    } else {
      null
    }
  }

  // Check if input matches a string at current position
  public matches(s: String): Boolean {
    var pi = pos;
    var si = String.begin;
    while (s.hasIndex(si)) {
      if (!chars.hasIndex(pi)) {
        return false;
      }
      if (chars[pi] != s[si]) {
        return false;
      }
      pi = chars.next(pi);
      si = s.next(si);
    }
    true
  }

  // Consume and return current character code point
  public advance(): Int {
    let c = chars[pos];
    pos = chars.next(pos);
    if (c == Chars.NEWLINE) {
      line = line + 1;
      column = 1;
    } else {
      column = column + 1;
    }
    c
  }

  // Consume n characters and return them as a string
  public advanceBy(n: Int): String {
    let start = pos;
    for (var i = 0; i < n; i += 1) {
      if (chars.hasIndex(pos)) {
        let c = chars[pos];
        pos = chars.next(pos);
        if (c == Chars.NEWLINE) {
          line = line + 1;
          column = 1;
        } else {
          column = column + 1;
        }
      }
    }
    chars.slice(start, pos)
  }

  // Get a slice from start position to current position
  public sliceFrom(start: StringIndex): String {
    chars.slice(start, pos)
  }

  // Get current location
  public location(): Location {
    new Location(line, column, 0)
  }

  // Record an error
  public error(msg: String): Void {
    errors.add("${line}:${column}: ${msg}");
  }

  // Add a token
  public addToken(tokenType: TokenType, value: String, start: Location): Void {
    let span = new Span(start, location());
    tokens.add(new Token(tokenType, value, span));
  }
}
```

## Main Tokenization Loop

The primary entry point for tokenization.

```temper
export let tokenize(input: String): List<Token> throws Bubble {
  let t = new Tokenizer(input);
  tokenizeAll(t);

  if (!t.errors.isEmpty) {
    // Errors collected in tokenizer - bubble to signal failure
    bubble()
  }

  t.tokens.toList()
}

let tokenizeAll(t: Tokenizer): Void {
  while (!t.isDone()) {
    tokenizeNext(t);
  }
  // Add EOF token
  t.addToken(TokenType.EOF, "", t.location());
}

let tokenizeNext(t: Tokenizer): Void {
  let c = t.peek();

  if (c == null) {
    return;
  }

  // Check for EEx expressions first (before < check)
  if (t.matches("<%")) {
    tokenizeEEx(t);
    return;
  }

  // Check for HTML comments
  if (t.matches("<!--")) {
    tokenizeComment(t);
    return;
  }

  // Check for tag start
  if (c == Chars.LT) {
    tokenizeTag(t);
    return;
  }

  // Check for expression start
  if (c == Chars.LBRACE) {
    tokenizeExpression(t);
    return;
  }

  // Otherwise, it's text content
  tokenizeText(t);
}
```

## Text Tokenization

Consume text until we hit a special character.

```temper
let tokenizeText(t: Tokenizer): Void {
  let start = t.location();
  let startPos = t.pos;

  while (!t.isDone()) {
    let c = t.peek();

    // Stop at special characters
    if (c == Chars.LT || c == Chars.LBRACE) {
      break;
    }

    t.advance();
  }

  let value = t.sliceFrom(startPos);
  if (!value.isEmpty) {
    t.addToken(TokenType.Text, value, start);
  }
}
```

## Tag Tokenization

Handle HTML tags, components, and slots.

```temper
let tokenizeTag(t: Tokenizer): Void {
  let start = t.location();

  // Consume <
  t.advance();

  // Check for closing tag
  let c = t.peek();
  if (c == Chars.SLASH) {
    t.advance();
    tokenizeClosingTag(t, start);
    return;
  }

  // Check for slot (:name)
  if (c == Chars.COLON) {
    t.advance();
    tokenizeSlotOpen(t, start);
    return;
  }

  // Check for local component (.name)
  if (c == Chars.DOT) {
    t.advance();
    tokenizeComponentOpen(t, start, true);
    return;
  }

  // Read tag/component name
  let name = readName(t);

  if (name.isEmpty) {
    t.error("Expected tag name after <");
    return;
  }

  // Check if it's a remote component (starts with uppercase)
  if (isRemoteComponent(name)) {
    t.addToken(TokenType.ComponentOpen, name, start);
  } else {
    t.addToken(TokenType.TagOpen, name, start);
  }

  // Tokenize attributes
  tokenizeAttributes(t);

  // Check for self-closing or end
  skipWhitespace(t);
  if (t.matches("/>")) {
    t.advanceBy(2);
    t.addToken(TokenType.TagSelfClose, "/>", t.location());
  } else if (t.peek() == Chars.GT) {
    t.advance();
    t.addToken(TokenType.TagEnd, ">", t.location());
  } else {
    t.error("Expected > or /> to close tag");
  }
}

let tokenizeClosingTag(t: Tokenizer, start: Location): Void {
  // Check for slot close (</:name>)
  let c = t.peek();
  if (c == Chars.COLON) {
    t.advance();
    let name = readName(t);
    skipWhitespace(t);
    if (t.peek() == Chars.GT) {
      t.advance();
    }
    t.addToken(TokenType.SlotClose, name, start);
    return;
  }

  // Check for local component close (</.name>)
  if (c == Chars.DOT) {
    t.advance();
    let name = readName(t);
    skipWhitespace(t);
    if (t.peek() == Chars.GT) {
      t.advance();
    }
    t.addToken(TokenType.ComponentClose, ".${name}", start);
    return;
  }

  // Regular tag or remote component close
  let name = readName(t);
  skipWhitespace(t);
  if (t.peek() == Chars.GT) {
    t.advance();
  }

  if (isRemoteComponent(name)) {
    t.addToken(TokenType.ComponentClose, name, start);
  } else {
    t.addToken(TokenType.TagClose, name, start);
  }
}

let tokenizeSlotOpen(t: Tokenizer, start: Location): Void {
  let name = readName(t);
  t.addToken(TokenType.SlotOpen, name, start);
  tokenizeAttributes(t);

  skipWhitespace(t);
  if (t.matches("/>")) {
    t.advanceBy(2);
    t.addToken(TokenType.TagSelfClose, "/>", t.location());
  } else if (t.peek() == Chars.GT) {
    t.advance();
    t.addToken(TokenType.TagEnd, ">", t.location());
  }
}

let tokenizeComponentOpen(t: Tokenizer, start: Location, isLocal: Boolean): Void {
  let name = readName(t);
  let fullName = if (isLocal) { ".${name}" } else { name };
  t.addToken(TokenType.ComponentOpen, fullName, start);
  tokenizeAttributes(t);

  skipWhitespace(t);
  if (t.matches("/>")) {
    t.advanceBy(2);
    t.addToken(TokenType.TagSelfClose, "/>", t.location());
  } else if (t.peek() == Chars.GT) {
    t.advance();
    t.addToken(TokenType.TagEnd, ">", t.location());
  }
}
```

## Attribute Tokenization

Handle static and dynamic attributes.

```temper
let tokenizeAttributes(t: Tokenizer): Void {
  while (!t.isDone()) {
    skipWhitespace(t);

    let c = t.peek();

    // End of attributes
    if (c == Chars.GT || c == Chars.SLASH || c == null) {
      break;
    }

    // Check for spread attribute {@attrs}
    if (c == Chars.LBRACE) {
      tokenizeSpreadAttribute(t);
      continue;
    }

    // Check for special attribute (:if, :for, :key)
    if (c == Chars.COLON) {
      tokenizeSpecialAttribute(t);
      continue;
    }

    // Regular attribute name
    let start = t.location();
    let name = readName(t);

    if (name.isEmpty) {
      t.error("Expected attribute name");
      t.advance(); // Skip bad character
      continue;
    }

    t.addToken(TokenType.AttrName, name, start);

    skipWhitespace(t);

    // Check for =
    if (t.peek() == Chars.EQUALS) {
      t.advance();
      t.addToken(TokenType.AttrEquals, "=", t.location());

      skipWhitespace(t);

      // Attribute value
      tokenizeAttributeValue(t);
    }
  }
}

let tokenizeAttributeValue(t: Tokenizer): Void {
  let start = t.location();
  let c = t.peek();

  // Dynamic value {expression}
  if (c == Chars.LBRACE) {
    tokenizeExpression(t);
    return;
  }

  // Quoted string value
  if (c == Chars.DQUOTE || c == Chars.SQUOTE) {
    let quote = t.advance();
    let startPos = t.pos;

    while (!t.isDone() && t.peek() != quote) {
      t.advance();
    }

    let value = t.sliceFrom(startPos);

    if (t.peek() == quote) {
      t.advance();
    } else {
      t.error("Unterminated string");
    }

    t.addToken(TokenType.AttrValue, value, start);
    return;
  }

  // Unquoted value (until whitespace or >)
  let startPos = t.pos;
  while (!t.isDone()) {
    let ch = t.peek();
    if (ch == null || isWhitespace(ch) || ch == Chars.GT || ch == Chars.SLASH) {
      break;
    }
    t.advance();
  }

  let value = t.sliceFrom(startPos);
  if (!value.isEmpty) {
    t.addToken(TokenType.AttrValue, value, start);
  }
}

let tokenizeSpreadAttribute(t: Tokenizer): Void {
  tokenizeExpression(t);
}

let tokenizeSpecialAttribute(t: Tokenizer): Void {
  let start = t.location();
  t.advance(); // Skip :

  let name = readName(t);
  t.addToken(TokenType.AttrName, ":${name}", start);

  skipWhitespace(t);

  if (t.peek() == Chars.EQUALS) {
    t.advance();
    t.addToken(TokenType.AttrEquals, "=", t.location());
    skipWhitespace(t);
    tokenizeAttributeValue(t);
  }
}
```

## Expression Tokenization

Handle {expression} interpolation.

```temper
let tokenizeExpression(t: Tokenizer): Void {
  let start = t.location();
  t.advance(); // Skip {

  t.addToken(TokenType.ExprOpen, "{", start);

  // Read until matching }
  let startPos = t.pos;
  var depth = 1;

  while (!t.isDone() && depth > 0) {
    let c = t.peek();

    if (c == Chars.LBRACE) {
      depth = depth + 1;
      t.advance();
    } else if (c == Chars.RBRACE) {
      depth = depth - 1;
      if (depth > 0) {
        t.advance();
      }
    } else if (c == Chars.DQUOTE || c == Chars.SQUOTE) {
      // Skip string contents
      let quote = c;
      t.advance();
      while (!t.isDone() && t.peek() != quote) {
        if (t.peek() == Chars.BACKSLASH) {
          t.advance();
        }
        if (!t.isDone()) {
          t.advance();
        }
      }
      if (!t.isDone()) {
        t.advance();
      }
    } else {
      t.advance();
    }
  }

  // Get content (excluding the final })
  let content = t.chars.slice(startPos, t.pos);
  t.addToken(TokenType.ExprContent, content, start);

  if (t.peek() == Chars.RBRACE) {
    t.advance();
    t.addToken(TokenType.ExprClose, "}", t.location());
  } else {
    t.error("Unterminated expression");
  }
}
```

## EEx Tokenization

Handle <% %> and <%= %> expressions.

```temper
let tokenizeEEx(t: Tokenizer): Void {
  let start = t.location();

  t.advanceBy(2); // Skip <%

  // Determine EEx type
  var eexType = TokenType.EExOpen;
  if (t.peek() == Chars.EQUALS) {
    t.advance();
    eexType = TokenType.EExOutput;
  } else if (t.peek() == Chars.HASH) {
    t.advance();
    eexType = TokenType.EExComment;
  }

  t.addToken(eexType, "", start);

  // Read content until %>
  let startPos = t.pos;

  while (!t.isDone() && !t.matches("%>")) {
    t.advance();
  }

  let content = t.sliceFrom(startPos);
  // Trim whitespace manually
  t.addToken(TokenType.EExContent, trimString(content), start);

  if (t.matches("%>")) {
    t.advanceBy(2);
    t.addToken(TokenType.EExClose, "%>", t.location());
  } else {
    t.error("Unterminated EEx expression");
  }
}

// Manual trim implementation
let trimString(s: String): String {
  var startIdx = String.begin;
  var endIdx = s.end;

  // Find first non-whitespace
  while (s.hasIndex(startIdx)) {
    let c = s[startIdx];
    if (!isWhitespace(c)) {
      break;
    }
    startIdx = s.next(startIdx);
  }

  // Find last non-whitespace
  while (s.hasIndex(s.prev(endIdx))) {
    let prevIdx = s.prev(endIdx);
    if (!s.hasIndex(prevIdx)) {
      break;
    }
    let c = s[prevIdx];
    if (!isWhitespace(c)) {
      break;
    }
    endIdx = prevIdx;
  }

  if (!s.hasIndex(startIdx)) {
    ""
  } else {
    s.slice(startIdx, endIdx)
  }
}
```

## Comment Tokenization

Handle <!-- --> HTML comments.

```temper
let tokenizeComment(t: Tokenizer): Void {
  let start = t.location();

  t.advanceBy(4); // Skip <!--
  t.addToken(TokenType.CommentOpen, "<!--", start);

  let startPos = t.pos;

  while (!t.isDone() && !t.matches("-->")) {
    t.advance();
  }

  let content = t.sliceFrom(startPos);
  t.addToken(TokenType.CommentContent, content, start);

  if (t.matches("-->")) {
    t.advanceBy(3);
    t.addToken(TokenType.CommentClose, "-->", t.location());
  } else {
    t.error("Unterminated comment");
  }
}
```

## Helper Functions

```temper
let readName(t: Tokenizer): String {
  let startPos = t.pos;

  // First character must be valid name start
  let firstChar = t.peek();
  when (firstChar) {
    is Int -> do {
      if (isNameStart(firstChar)) {
        t.advance();

        // Rest can be name chars
        while (!t.isDone()) {
          let nextChar = t.peek();
          when (nextChar) {
            is Int -> do {
              if (isNameChar(nextChar)) {
                t.advance();
              } else {
                break;
              }
            };
            else -> break;
          }
        }
      }
    };
    else -> void;
  }

  t.sliceFrom(startPos)
}

let skipWhitespace(t: Tokenizer): Void {
  while (!t.isDone()) {
    let c = t.peek();
    if (c != null && isWhitespace(c)) {
      t.advance();
    } else {
      break;
    }
  }
}
```
