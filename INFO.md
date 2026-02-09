# HEEx in Temper - Research Cache

## Project Goal
Implement HEEx (Phoenix LiveView's HTML+EEx templating language) in Temper, using Temper's literate programming paradigm.

---

## Temper Language Summary

### Core Concepts
- **Cross-compiles** to Java, JavaScript, Python, C#, Lua, Rust
- **Literate programming** via `.temper.md` files (Markdown with embedded code)
- **Strong typing** with inference, generics, interfaces
- **Immutable by default** (`let` for constants, `var` for mutable)

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

// Pattern matching
when (node) {
  is TextNode -> node.text;
  is Element -> "<" + node.tag + ">";
  else -> "";
}

// Error handling
let risky(): String throws Bubble { ... }
```

### Module Structure
```
project/
  config.temper.md     # Package metadata + imports
  parser.temper.md     # Main module code
  tests/               # Test files
```

### Parser Patterns (from temper-regex-parser)
1. **Recursive descent** with stateful `Parser` class
2. **State**: `chars` (input), `pos` (position), `errors` (ListBuilder)
3. **Hierarchy**: `readTop()` → `readSeq()` → `readSingle()`
4. **Optimization**: Buffer consecutive characters into single nodes
5. **Error collection**: Non-fatal errors via `ListBuilder<String>`

---

## HEEx Architecture Summary

### Three-Layer Pipeline
1. **Tokenizer** → tokens (`:tag`, `:close`, `:text`, `:body_expr`, `:eex`)
2. **Parser** → hierarchical AST (blocks, components, slots)
3. **Compiler** → executable code (Elixir AST)

### Core Syntax Elements

#### HTML Tags
```heex
<div class="container">
  <p>Content</p>
</div>
```

#### Dynamic Attributes
```heex
<div id={@user_id} class={["base", @dynamic]}>
<div {@attrs}>  <!-- Attribute spread -->
```

#### Interpolation
```heex
{@variable}           <!-- Curly brace syntax (inside tags) -->
<%= expression %>     <!-- EEx syntax (body content) -->
```

#### Components
```heex
<.local_component name="value" />     <!-- Local (same module) -->
<Remote.Component name="value" />     <!-- Remote (other module) -->
```

#### Slots
```heex
<.card>
  Default content (inner_block)
  <:header>Named slot content</:header>
</.card>
```

#### Special Attributes
```heex
<div :if={@show}>     <!-- Conditional rendering -->
<li :for={item <- @items} :key={item.id}>  <!-- List comprehension -->
```

#### EEx Blocks
```heex
<%= if @condition do %>
  <p>True branch</p>
<% else %>
  <p>False branch</p>
<% end %>
```

### Token Types
| Token | Example |
|-------|---------|
| `:tag` | `<div`, `<.component`, `<:slot` |
| `:close` | `</div>`, `</.component>`, `</:slot>` |
| `:text` | Plain text content |
| `:body_expr` | `{@variable}` in body |
| `:attr_expr` | `{value}` in attributes |
| `:eex` | `<%= ... %>`, `<% ... %>` |
| `:eex_comment` | `<%# ... %>` |

### Component Naming Convention
- **`.name`** → local function call
- **`Name`** (capitalized) → remote module call
- **`:name`** → named slot

---

## Implementation Strategy

### Phase 1: AST Definitions
Define node types for:
- `Document` - root container
- `Element` - HTML tags with attributes
- `Component` - local/remote components
- `Slot` - named slots
- `Text` - static text
- `Expression` - `{...}` interpolation
- `EExBlock` - `<% ... %>` blocks
- `Attribute` - static or dynamic

### Phase 2: Tokenizer
Implement state machine for:
1. Text content
2. Tag opening (`<`, `</`, `<.`, `<:`)
3. Tag names and attributes
4. Expression delimiters (`{`, `}`, `<%`, `%>`)
5. Comments (`<%#`, `<!-- -->`)

### Phase 3: Parser
Recursive descent parser:
1. `parseDocument()` → list of top-level nodes
2. `parseElement()` → tag + attributes + children
3. `parseComponent()` → local/remote detection
4. `parseSlot()` → named slot handling
5. `parseExpression()` → curly brace content
6. `parseEEx()` → `<% %>` block content

### Phase 4: Renderer
Convert AST back to:
- HTML string output
- Target language code (for compilation)

---

## File Structure Plan

```
heex/
  config.temper.md      # Package metadata
  ast.temper.md         # Node type definitions
  tokenizer.temper.md   # Lexical analysis
  parser.temper.md      # Syntax analysis
  renderer.temper.md    # Code generation
  exports.temper.md     # Public API
  tests/
    tokenizer.temper    # Tokenizer tests
    parser.temper       # Parser tests
    integration.temper  # End-to-end tests
```

---

## Key Design Decisions

### 1. Expression Handling
HEEx has two interpolation syntaxes:
- `{...}` - attribute-safe, HTML-aware
- `<%= ... %>` - EEx compatibility

Decision: Parse both, normalize internally to expression nodes.

### 2. Component Resolution
Components can be local (`.name`) or remote (`Module.name`).

Decision: Store component type in AST node, resolve at render time.

### 3. Slot Scope
Slots can have `:let` bindings for data passing.

Decision: Model as scoped expressions with parameter binding.

### 4. Error Recovery
Should tokenizer/parser stop on first error or collect all?

Decision: Collect errors (like temper-regex-parser) for better DX.

### 5. Whitespace Handling
HTML whitespace is significant in some contexts.

Decision: Preserve whitespace in text nodes, trim intelligently.

---

## Current Progress (Session Paused)

### Files Created
- [x] `heex/config.temper.md` - Package metadata and imports
- [x] `heex/ast.temper.md` - Complete AST node definitions
  - `Node` interface, `Location`, `Span` for source tracking
  - `Document`, `Text`, `Element`, `Component`, `Slot`
  - `Expression`, `EEx`, `EExBlock`, `EExClause`, `Comment`
  - `Attribute` hierarchy: Static, Dynamic, Spread, Special
- [x] `heex/tokenizer.temper.md` - Complete tokenizer implementation
  - `Token`, `TokenType` enum (20+ token types)
  - `Tokenizer` class with state management
  - All tokenization functions for tags, attributes, expressions, EEx
- [x] `heex/parser.temper.md` - Complete parser implementation
  - `Parser` class with token consumption
  - Recursive descent parsing for all node types
  - EEx block handling (if/else/case/for)
- [x] `heex/renderer.temper.md` - Complete renderer implementation
  - `renderHtml()` - HTML string output
  - `renderDebug()` - AST visualization
  - `renderJson()` - JSON serialization

### Files Not Yet Created
- [ ] `heex/exports.temper.md` - Public API surface
- [ ] `heex/tests/tokenizer.temper` - Tokenizer unit tests
- [ ] `heex/tests/parser.temper` - Parser unit tests
- [ ] `heex/tests/integration.temper` - End-to-end tests

### Next Steps
1. Create exports.temper.md with public API
2. Write test files
3. Test with actual Temper compiler (if available)
4. Iterate on edge cases

---

## Decision Graph Summary

Run `deciduous nodes` to see all 22 logged nodes including:
- Goal: Implement HEEx in Temper (node 1)
- Research actions (nodes 9, 12, 15, 19)
- Observations from each research area
- Implementation decision (node 8)
- Project structure creation action/outcome (nodes 21-22)

Run `deciduous edges` to see the graph connections.

---

## References

- **Temper docs**: `docs/for-users/temper-docs/docs/`
- **Temper regex parser**: `temper-regex-parser/`
- **Prismora color lib**: `prismora/`
- **Phoenix LiveView HEEx**: `phoenix_live_view/lib/phoenix_live_view/tag_engine/`
- **VSCode HEEx grammar**: `vscode-html-heex/`
