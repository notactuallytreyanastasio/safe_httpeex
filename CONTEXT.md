# safe_httpeex — Knowledge Cache

This document captures everything needed to build a new HEEx template parser from scratch using Temper's **safe HTML templating** features (tagged strings / StringExprMacro). It is a comprehensive reference derived from the original `httpeex` project and the `Anneal` learning platform built around it.

---

## Table of Contents

1. [Project Goal](#project-goal)
2. [What is HEEx?](#what-is-heex)
3. [Temper Language Reference](#temper-language-reference)
4. [Safe Templating: Tagged Strings / StringExprMacro](#safe-templating)
5. [Original httpeex Architecture](#original-httpeex-architecture)
6. [AST Node Definitions (Reference)](#ast-node-definitions)
7. [Tokenizer Design (Reference)](#tokenizer-design)
8. [Parser Design (Reference)](#parser-design)
9. [Renderer Design (Reference)](#renderer-design)
10. [Test Suite (Reference)](#test-suite)
11. [Build & Toolchain](#build--toolchain)
12. [CI/CD Distribution Pipeline](#cicd-distribution-pipeline)
13. [Anneal Learning Platform Context](#anneal-learning-platform-context)
14. [Temper Error Output Format](#temper-error-output-format)
15. [Key Gotchas & Lessons Learned](#key-gotchas--lessons-learned)

---

## Project Goal

Reimplement the HEEx template parser using Temper's **new safe HTML templating** features — specifically the tagged string / `StringExprMacro` system that provides **compile-time XSS prevention**. The original `httpeex` parser works and compiles to 6 languages, but it uses basic string concatenation for HTML output. The new implementation should use `appendSafe()` for trusted literal HTML parts and `append()` for untrusted user input, providing **type-level distinction** between safe markup and user data.

This new project:
1. Lives in `httpeex/safe_httpeex/` alongside the original
2. Uses the original as reference implementation (same feature set)
3. Leverages the newer Temper toolchain with tagged string support
4. Will become capstone lesson content for the Anneal learning platform

---

## What is HEEx?

**HEEx** (HTML + EEx) is the templating language used by [Phoenix LiveView](https://github.com/phoenixframework/phoenix_live_view). It extends Elixir's EEx with HTML-aware features.

### Core Syntax Elements

```heex
<!-- HTML Elements -->
<div class="container">content</div>
<input type="text" />

<!-- Dynamic Attributes -->
<div id={@user_id} class={["base", @dynamic]}>
<div {@attrs}>  <!-- Attribute spread -->

<!-- Interpolation -->
{@variable}           <!-- Curly brace syntax -->
<%= expression %>     <!-- EEx syntax -->

<!-- Components -->
<.local_component name="value" />     <!-- Local (same module, starts with .) -->
<Remote.Component name="value" />     <!-- Remote (other module, starts with uppercase) -->

<!-- Slots -->
<.card>
  Default content (inner_block)
  <:header>Named slot content</:header>
  <:footer :let={data}>Footer with data</:footer>
</.card>

<!-- Special Attributes -->
<div :if={@show}>     <!-- Conditional rendering -->
<li :for={item <- @items} :key={item.id}>  <!-- List comprehension -->

<!-- EEx Blocks -->
<%= if @condition do %>
  <p>True branch</p>
<% else %>
  <p>False branch</p>
<% end %>
```

### Component Naming Convention
- **`.name`** → local function call (starts with dot)
- **`Name`** (capitalized first char) → remote module call
- **`:name`** (colon prefix) → named slot

### Token Types
| Token | Example |
|-------|---------|
| Text | Plain text content |
| TagOpen | `<div` |
| TagClose | `</div>` |
| TagSelfClose | `/>` |
| TagEnd | `>` |
| ComponentOpen | `<.button`, `<MyApp.Button` |
| ComponentClose | `</.button>`, `</MyApp.Button>` |
| SlotOpen | `<:header` |
| SlotClose | `</:header>` |
| AttrName | `class`, `:if` |
| AttrEquals | `=` |
| AttrValue | `"value"` |
| ExprOpen | `{` |
| ExprClose | `}` |
| ExprContent | content inside `{}` |
| EExOpen | `<%` |
| EExOutput | `<%=` |
| EExComment | `<%#` |
| EExClose | `%>` |
| EExContent | content inside `<% %>` |
| CommentOpen | `<!--` |
| CommentClose | `-->` |
| CommentContent | content inside comments |
| EOF | end of input |

---

## Temper Language Reference

### Core Concepts
- **Cross-compiles** to Java, JavaScript, Python, C#, Lua, Rust
- **Literate programming** via `.temper.md` files (Markdown with embedded code in fenced blocks)
- **Strong typing** with inference, generics, interfaces
- **Immutable by default** (`let` for constants, `var` for mutable)
- **Directory = Module**: All `.temper.md` files in a directory are automatically combined into ONE module

### Module System (Critical)
- All `.temper.md` files in a directory → ONE module
- Cannot use `import("./file")` for files in same directory — only subdirectories work
- Parent imports: `import("..")` to import from parent module
- Config imports: `import(".")` for main module, `import("./tests")` for test submodule
- `config.temper.md` defines package metadata and imports

### Key Syntax

```temper
// Functions
let add(a: Int, b: Int): Int { a + b }
export let multiply(a: Int, b: Int): Int { a * b }

// Classes (properties in constructor)
class Parser(
  public chars: String,
  public var pos: Int,
) {
  public advance(): Void { pos = pos + 1; }
}

// Interfaces (can have default implementations)
interface Node { render(): String; }

// Inheritance
class Element(public tag: String) extends Node {
  public render(): String { "<${tag}>" }
}

// Pattern matching (type narrowing)
when (node) {
  is Text -> node.content;          // node narrowed to Text type
  is Element -> "<${node.tag}>";    // node narrowed to Element type
  else -> "";
}

// Error handling
let risky(): String throws Bubble { bubble() }
// Must declare `throws Bubble` to call bubble()

// Loops
for (let item of list) { ... }     // NOT `for (item in list)` — that's invalid!
for (var i = 0; i < n; i += 1) { ... }

// Lists
let items = new ListBuilder<String>();
items.add("hello");
let list = items.toList();

// String builder
let out = new StringBuilder();
out.append("hello");
out.appendCodePoint(c) orelse void;
out.toString()

// Nullable
let x: String? = null;
when (x) {
  is String -> x.length;   // safe access
  else -> 0;
}

// Test blocks
test("my test") {
  assert(1 + 1 == 2);
}
```

### String API (Critical — No `.length` on String!)
Temper strings use `StringIndex` for iteration — there is NO `.length` property on String.

```temper
// Iteration
var idx = String.begin;
while (s.hasIndex(idx)) {
  let c: Int = s[idx];           // Returns code point (Int)
  idx = s.next(idx);
}

// Common operations
s.isEmpty                        // Check if empty
s.hasIndex(idx)                  // Check if index is valid
s[idx]                          // Get code point at index (returns Int)
s.next(idx)                     // Next index
s.prev(idx)                     // Previous index (for reverse iteration)
s.end                           // End sentinel index
s.slice(startIdx, endIdx)       // Substring by index range

// Character literals
char'x'                          // Returns Int (code point value)
char'<'                          // == 60
char'\n'                         // == 10

// String interpolation
"Hello, ${name}!"               // NOT "Hello, " + name
```

### Pattern Matching Rules
- Use `when (value) { is Type -> ... }` for type-safe narrowing
- **Cannot** use `is "string"` for string values — use `== "string"` with if/else
- The `when` body narrows the variable to the matched type

### Exception Handling
- Use `bubble()` not `throw new Bubble(...)`
- Functions must declare `throws Bubble` to call `bubble()`
- Tests can use `assert(condition)` but only inside `test` blocks
- `assert` is NOT supported in regular functions for JS backend
- `orelse` handles errors: `riskyCall() orelse fallbackValue`

---

## Safe Templating

### Tagged Strings / StringExprMacro

Temper's new feature for **compile-time XSS prevention**. The key insight:

- **`appendSafe(literal)`** — for trusted HTML fragments (template literals)
- **`append(userInput)`** — for untrusted user data (gets auto-escaped)

The type system distinguishes between safe and unsafe string fragments at compile time, making XSS impossible by construction rather than by runtime escaping.

### Accumulator Pattern

```temper
// Safe HTML builder (conceptual)
let builder = new SafeHtmlBuilder();
builder.appendSafe("<div class=\"");     // Trusted literal
builder.append(userProvidedClass);       // Untrusted — auto-escaped
builder.appendSafe("\">");              // Trusted literal
builder.append(userContent);            // Untrusted — auto-escaped
builder.appendSafe("</div>");          // Trusted literal
```

### Implementation Notes
- The old renderer in `httpeex` uses plain `StringBuilder.append()` for everything
- The new implementation should use the safe builder pattern
- This affects primarily the renderer module — tokenizer and parser stay largely the same
- The AST definitions should track which parts are safe vs user-provided

---

## Original httpeex Architecture

### Three-Stage Pipeline
```
Raw Template String
       ↓
   Tokenizer (tokenizer.temper.md)
       ↓
   Token Stream (List<Token>)
       ↓
   Parser (parser.temper.md)
       ↓
   AST (Document with children)
       ↓
   Renderer (renderer.temper.md)
       ↓
   Output (HTML / Debug / JSON)
```

### File Structure
```
heex/
  config.temper.md      # Package metadata (name, version, backend configs, imports)
  ast.temper.md         # AST node definitions (363 lines)
  tokenizer.temper.md   # Lexical analysis (839 lines)
  parser.temper.md      # Recursive descent parser (748 lines)
  renderer.temper.md    # HTML/Debug/JSON output (618 lines)
  exports.temper.md     # Public API (126 lines)
  tests/
    imports.temper.md   # let { ... } = import("..");
    tokenizer.temper.md # 14 tokenizer tests
    parser.temper.md    # 18 parser tests
    integration.temper.md # 12 roundtrip + rendering tests
```

### Total: ~2,769 lines of Temper source across 6 files

---

## AST Node Definitions

### Type Hierarchy

```
Node (interface)
├── Document (children: List<Node>, span: Span?)
├── Text (content: String, span: Span?)
├── Element (tag: String, attributes: List<Attribute>, children: List<Node>, selfClosing: Boolean, span: Span?)
├── Component (componentType: ComponentType, name: String, attributes: List<Attribute>, children: List<Node>, slots: List<Slot>, span: Span?)
├── Slot (name: String, attributes: List<Attribute>, children: List<Node>, letBinding: String?, span: Span?)
├── Expression (code: String, span: Span?)
├── EEx (eexType: EExType, code: String, span: Span?)
├── EExBlock (blockType: String, expression: String, clauses: List<EExClause>, span: Span?)
└── Comment (content: String, span: Span?)

Attribute (interface)
├── StaticAttribute (name: String, value: String, span: Span?)
├── DynamicAttribute (name: String, expression: Expression, span: Span?)
├── SpreadAttribute (expression: Expression, span: Span?)
└── SpecialAttribute (kind: String, expression: Expression, span: Span?)

Location (line: Int, column: Int, offset: Int)
Span (start: Location, end: Location)

ComponentType: Local | Remote (static instances)
EExType: Output | Exec | Comment (static instances)
EExClause (clauseType: String, expression: String?, children: List<Node>, span: Span?)
```

### Helper Functions
- `isVoidElement(tag)` — checks void HTML5 elements (br, hr, img, input, etc.)
- `isLocalComponent(name)` — starts with `.`
- `isRemoteComponent(name)` — starts with uppercase A-Z
- `isSlot(name)` — starts with `:`

### Full Source
See `../heex/ast.temper.md` (363 lines) for the complete implementation.

---

## Tokenizer Design

### Architecture
- **Stateful `Tokenizer` class** with: `chars` (input string), `pos` (StringIndex), `line`/`column` (1-based)
- **Error collection**: `ListBuilder<String>` for non-fatal errors
- **Token output**: `ListBuilder<Token>` built incrementally

### Character Constants
Defined in a `Chars` class with static constants:
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
  public static let NEWLINE: Int = char'\n';
  public static let SPACE: Int = char' ';
  // ... etc
}
```

### Main Loop
```
tokenizeAll → tokenizeNext (dispatches based on first char):
  - "<%"  → tokenizeEEx
  - "<!--" → tokenizeComment
  - '<'   → tokenizeTag (handles elements, components, slots, closing tags)
  - '{'   → tokenizeExpression
  - else  → tokenizeText
```

### Key Methods on Tokenizer
- `peek()` → current char code point (nullable)
- `peekAhead(n)` → look ahead n chars
- `matches(s)` → check if input matches string at current position
- `advance()` → consume one char, update line/column
- `advanceBy(n)` → consume n chars
- `sliceFrom(startPos)` → get substring from start to current
- `addToken(type, value, startLoc)` → emit a token

### Tag Tokenization Flow
```
tokenizeTag:
  '<' consumed
  → '/' → tokenizeClosingTag (handles tag/component/slot close)
  → ':' → tokenizeSlotOpen
  → '.' → tokenizeComponentOpen (local)
  → name → TagOpen or ComponentOpen (if uppercase)
  → tokenizeAttributes
  → '/>' (self-close) or '>' (tag end)
```

### Expression Tokenization
Tracks brace depth for nested `{}` in expressions. Handles string literals inside expressions (skips quoted content to avoid false brace matches).

### Full Source
See `../heex/tokenizer.temper.md` (839 lines) for the complete implementation.

---

## Parser Design

### Architecture
- **Recursive descent parser** with token list and integer position
- **Error-tolerant**: collects errors via `ListBuilder<String>` rather than failing fast
- **Builds hierarchical AST** from flat token stream

### String Helpers (Required)
The parser needs several string helper functions since Temper strings lack built-in methods:
- `stringStartsWith(s, prefix)` — character-by-character comparison
- `stringEndsWith(s, suffix)` — reverse comparison
- `stringContains(s, sub)` — sliding window search
- `stringTrim(s)` — strip leading/trailing whitespace
- `splitFirstWord(s)` — split on first space, returns `[word, rest]`
- `stringSliceFromOffset(s, n)` — substring from character offset
- `stringDropLast(s, n)` — remove last n characters

### Parsing Flow
```
parse(input) → tokenize → parseTokens → parseChildren(closingTag=null)

parseChildren loops:
  - Check for closing tag → break
  - parseNode dispatches on token type:
    - text → parseText
    - tag_open → parseElement
    - component_open → parseComponent
    - slot_open → parseSlot
    - expr_open → parseExpression
    - eex_open/eex_output → parseEEx
    - comment_open → parseComment

parseElement:
  - Consume TagOpen
  - parseAttributes
  - Self-close (TagSelfClose) or TagEnd
  - If void element → no children
  - Else → parseChildren(tagName) + expect TagClose

parseComponent:
  - Consume ComponentOpen
  - Determine Local vs Remote
  - parseAttributes
  - parseComponentBody → separates children from slots
  - Expect ComponentClose

parseEEx:
  - Check if block start (if/case/cond/for/unless)
  - If block → parseEExBlock with clauses (do/else/end)
  - Else → simple EEx node
```

### Full Source
See `../heex/parser.temper.md` (748 lines) for the complete implementation.

---

## Renderer Design

### Three Output Modes

**1. HTML Rendering (`renderHtml`)**
- Recursive AST walk with pattern matching (`when (node) { is Element -> ... }`)
- Escapes content for XSS prevention (`escapeHtml`, `escapeAttr`)
- Preserves expressions as `{...}` placeholders
- Self-closes void elements

**2. Debug Rendering (`renderDebug`)**
- Pretty-prints AST with indentation
- Shows node types, attribute details, structure
- Escapes newlines for readability

**3. JSON Serialization (`renderJson`)**
- Full AST as structured JSON
- Includes type info, attributes, children relationships
- For tooling integration

### HTML Escaping
```temper
escapeHtml: & → &amp;, < → &lt;, > → &gt;
escapeAttr: & → &amp;, " → &quot;, < → &lt;, > → &gt;
```

### Full Source
See `../heex/renderer.temper.md` (618 lines) for the complete implementation.

---

## Test Suite

### Test Structure
```
tests/
  imports.temper.md      # let { ... } = import("..");
  tokenizer.temper.md    # 14 tests
  parser.temper.md       # 18 tests
  integration.temper.md  # 12 tests
```
**Total: 44 tests**

### Tokenizer Tests
- Plain text, whitespace
- Opening/closing/self-closing tags
- Single and multiple attributes
- Expressions, dynamic attributes
- EEx output/eval/comment
- Local/remote components
- Slot open/close
- HTML comments

### Parser Tests
- Plain text, empty document
- Simple/self-closing/void/nested elements, elements with text
- Static/multiple/dynamic/spread/special attributes
- Local/remote/self-closing components, components with children
- Named slots, multiple slots
- Text with expression, expression in element
- EEx output/eval/comment/block
- HTML comments

### Integration Tests
- Roundtrip: parse → renderHtml → parse again (idempotence)
- HTML roundtrips: text, elements, attributes, nested, void
- Component roundtrips: local, remote, with slots
- Expression roundtrips
- Debug rendering produces output
- JSON rendering produces valid structure

### Important: Tests Don't Run in the REPL!
Temper `test("...") { assert(...); }` blocks are compiled and **registered** but **not executed** in the REPL. They only run via `temper test` or `temper build`. The REPL returns `void` even for failing assertions.

---

## Build & Toolchain

### Requirements
- **Java 21** (required by Temper compiler)
  - macOS: `/opt/homebrew/opt/openjdk@21`
- **Temper CLI** from https://github.com/temperlang/temper

### Dual Toolchain (on this machine)
- `temper-old` (0.6.1-dev+27-g613490b) — original version used for httpeex
- `temper` (0.6.1-dev+48-gdb43268) — latest main with tagged string support
- Both at `~/.local/bin/` with JAVA_HOME wrapper scripts

### Build Commands
```bash
# Build all backends
JAVA_HOME=/opt/homebrew/opt/openjdk@21 temper build -b js -b py -b java -b csharp -b lua -b rust

# Build single backend
JAVA_HOME=/opt/homebrew/opt/openjdk@21 temper build -b js

# Force rebuild
JAVA_HOME=/opt/homebrew/opt/openjdk@21 temper build -b js --rerun-tasks

# Clean build (delete caches first)
rm -rf temper.out temper.keep
JAVA_HOME=/opt/homebrew/opt/openjdk@21 temper build -b js

# REPL for testing
echo 'let x = 5; x + 3;' | temper repl --separator eof --prompt hide 2>&1
# Output: interactive#0: 8
```

### Output Structure
```
temper.out/
  js/heex/        # npm package (828 KB)
  py/heex/        # setuptools package (824 KB)
  java/heex/      # Maven/Gradle project (3.4 MB)
  csharp/heex/    # .NET project (3.5 MB)
  lua/heex/       # Lua modules (984 KB)
  rust/heex/      # Cargo crate (1.3 MB)
```

---

## CI/CD Distribution Pipeline

### Build Workflow (`.github/workflows/build.yml`)
- Triggers on push to main + manual dispatch
- Sets up Java 21, clones Temper repo, builds CLI
- Runs `temper build -b js -b py -b java -b csharp -b lua -b rust`
- Uploads 6 artifacts (one per language)

### Distribute Workflow (`.github/workflows/distribute.yml`)
- Triggers after successful build
- Downloads artifacts, pushes to language-specific repos:
  - `notactuallytreyanastasio/heex-{js,py,java,csharp,lua,rs}`
- Uses GitHub App token for cross-repo push
- Tags all sub-repos with version from `VERSION` file
- Uses rsync to sync generated code to `src/` in each sub-repo

---

## Anneal Learning Platform Context

### What is Anneal?
A Phoenix LiveView application that teaches Temper programming through interactive exercises. The httpeex parser serves as lesson content — students learn Temper by studying and building a real parser.

### Tech Stack
- Phoenix 1.8.3 + LiveView 1.1.0
- Ecto + PostgreSQL
- Tailwind CSS v4
- Docker (sandboxed Temper REPL execution)

### Key Features Built
- **Progressive disclosure**: Lesson content split by `---`, revealed section by section
- **Fill-in-the-blank exercises**: `temper_fill` code blocks with `[blank_id]` placeholders
- **Code evaluation**: Textarea + Run button, async Temper REPL execution
- **SM-2 spaced repetition**: ease_factor, interval_days, repetition_count on UserProgress
- **Lesson DAG**: Prerequisites via many-to-many join table, locked/available/completed states
- **Temper syntax highlighting**: Written in Temper, compiled to JS, integrated as LiveView hook
- **Session tracking**: LessonSession with visit_number, visit_type, visible_section
- **Resumable progress**: Reconstruct correct_blanks from DB answers on reconnect
- **Glossary tooltips**: Auto-annotate Temper terms with hover definitions
- **Real-time validation**: Per-blank Enter/blur validation with green/red glow shadows

### Current Lesson Structure (6 lessons, 2 branches)
```
Branch A: Functions                    Branch B: Data Types
A1: Your First Function (root)        B1: Strings & Interpolation (root)
 └── A2: Control Flow                  └── B2: Classes & Methods
      └── A3: Pattern Matching              └── B3: Interfaces & Types
```

### Pending Anneal Work
1. **Fill-in-the-blank first** — A1/B1 should be fill_blank, not code_eval
2. **Structured Temper error parsing** — replace string manipulation with proper parser
3. **Compiler error exercises** — new exercise type where users fix broken code
4. **Show failing tests** — display test code and results to guide learners
5. **Validation code approach** — REPL can't run `test()` blocks, need REPL-executable validation expressions

---

## Temper Error Output Format

### Error Message Structure
```
<source line display with visual indicator>
[<location>]@<phase>: <message>
```

### Visual Indicators
- **Span indicator**: `┗━━━┛` — underlines a range of characters
- **Point indicator**: `⇧` — points to a single character position

### Location Format
```
[<file>#<chunk>:<line>+<start_col>-<end_col>]@<phase>: <message>
```
- `file`: Source identifier ("interactive" in REPL)
- `chunk`: Integer chunk number (e.g., `#0`)
- `line`: 1-based line number
- `start_col`: 0-based start column
- `end_col`: 0-based end column (exclusive); just `+col` for single char
- `phase`: Compiler phase code (see below)

### Compiler Phase Codes
| Code | Phase | When It Fires |
|------|-------|---------------|
| `@P` | Parse | Syntax errors (unclosed brackets, malformed structure) |
| `@G` | GenerateCode | Type errors, undefined variables/methods, signature mismatches |
| `@R` | Run | Runtime errors (type rejections, panics) |
| `@I` | Import | Failed imports |

### Error Examples

**Type mismatch:**
```
1: let x: Int = "hello";
                ┗━━━━━┛
[interactive#0:1+13-20]@G: Cannot assign to Int32 from String
```

**Undefined variable:**
```
1: let y = unknownVar;
           ┗━━━━━━━━┛
[interactive#0:1+8-18]@G: No declaration for unknownVar
```

**Wrong argument types:**
```
1: 1 + "hello";
       ┗━━━━━┛
[interactive#0:1+4-11]@G: Actual arguments do not match signature: (Int32, Int32) -> Int32 expected [Int32, Int32], but got [Int32, String]
```

### Result Line
Every REPL chunk ends with:
```
interactive#0: fail     -- errors occurred
interactive#0: void     -- success (no return value)
interactive#0: <value>  -- success with value
```

### Cascading Errors
A single issue often produces multiple errors from different phases. E.g., a type mismatch produces both a `@G` error ("Cannot assign to X from Y") and an `@R` error ("Type X rejected value Y").

---

## Key Gotchas & Lessons Learned

### Temper-Specific
1. **`for (entry in list)` is INVALID** — Temper uses `for (let x of list)`. The `in` keyword doesn't exist.
2. **No `.length` on String** — Must iterate with `StringIndex`. Only `List` has `.length`.
3. **String interpolation is `"${var}"`** — Not `"prefix" + var`.
4. **`char'x'` returns `Int`** — It's a code point, not a character type.
5. **`bubble()` not `throw`** — And the function must declare `throws Bubble`.
6. **`assert` only works in `test` blocks** — Not in regular functions (JS backend limitation).
7. **Tests don't run in the REPL** — They register but don't execute. REPL returns `void`.
8. **Directory = module** — All `.temper.md` files in a dir are one module. Can't import sibling files.
9. **Nested code fences in literate Temper** — Use 4 backticks for outer fence when inner content has triple backticks.
10. **`ListBuilder` not array literals for building lists** — `new ListBuilder<T>()`, `.add()`, `.toList()`.
11. **`StringBuilder` for string building** — `new StringBuilder()`, `.append()`, `.toString()`.
12. **`appendCodePoint(c) orelse void`** — Code point append can fail, must handle with `orelse`.
13. **`when` with `is` narrows the type** — After `is Element`, the variable is typed as `Element`.
14. **Pattern matching on values (not types)** — Use `==` with if/else, not `is "string"`.
15. **Static instances, not enums** — `ComponentType.Local` is `new ComponentType("local")`, not an enum.

### Build/Toolchain
1. **Java 21 required** — Set `JAVA_HOME=/opt/homebrew/opt/openjdk@21` on macOS.
2. **Clean builds** — Delete `temper.out` and `temper.keep` before rebuilding if things get stale.
3. **esbuild for bundling** — Use `--alias:@temperlang/core=./path/to/temper-core/index.js` for resolving Temper runtime.
4. **`--rerun-tasks`** — Forces Gradle to rebuild even if it thinks nothing changed.

### Architecture
1. **Error-tolerant parsing** — Collect errors instead of failing fast. Better DX.
2. **Three-stage pipeline** — Tokenize → Parse → Render. Clean separation of concerns.
3. **StringIndex iteration pattern** — The standard Temper idiom for processing strings char by char.
4. **Static class pattern for "enums"** — Temper doesn't have real enums; use static instances on a class.
