# Comparison Report: safe_httpeex vs httpeex-accumulator

Two independent approaches to adding type-safe HTML rendering to the httpeex HEEx parser.

---

## Architecture Summary

### safe_httpeex — "Replace the renderer"

Replaces the original `StringBuilder`-based renderer wholesale with a `SafeHtmlBuilder` accumulator. There is **one renderer**, and it is the safe one.

| File | Lines | Role |
|------|-------|------|
| `safe_html.temper.md` | 125 | SafeHtmlBuilder class + escapeHtml |
| `renderer.temper.md` | 594 | Single renderer using SafeHtmlBuilder |
| `exports.temper.md` | 135 | Exports SafeHtmlBuilder for tagged strings |
| **Source total** | **2,885** | 7 source files |
| **Test total** | **647** | 4 test files, 80 tests |

### httpeex-accumulator — "Add safety alongside"

Keeps the original `StringBuilder`-based renderer intact and adds a parallel safe rendering system: both a compile-time accumulator (`HtmlBuilder`/`AttrBuilder`) and a runtime type wrapper (`HtmlSafe`/`AttrSafe`).

| File | Lines | Role |
|------|-------|------|
| `html-accumulator.temper.md` | 132 | HtmlBuilder + AttrBuilder accumulators |
| `html-safe.temper.md` | 140 | HtmlSafe + AttrSafe runtime wrappers |
| `renderer-safe.temper.md` | 271 | Parallel safe renderer using HtmlSafe |
| `renderer.temper.md` | 618 | Original renderer (manual escapeHtml) |
| `exports.temper.md` | 126 | Does **not** export safe renderer |
| **Source total** | **3,401** | 12 source files |
| **Test total** | **475** | 4 test files + 2 safety test files |

---

## Key Differences

### 1. Safety Integration: All-in vs Opt-in

**safe_httpeex** makes safety the default and only path. The renderer function signature is:
```temper
export let renderHtml(doc: Document): String {
  let out = new SafeHtmlBuilder();          // <-- accumulator
  for (let child of doc.children) {
    renderNode(child, out);
  }
  out.accumulated
}
```

Every call to `renderHtml` is safe. There is no unsafe path.

**httpeex-accumulator** keeps both. The original `renderHtml` still uses `StringBuilder` with manual `escapeHtml()` calls. The safe renderer is a separate function (`renderHtmlSafe`) in a separate file (`renderer-safe.temper.md`) — and it is **not exported** in `exports.temper.md`. A consumer would have to know about it and import it specifically.

### 2. Escaping Strategy

**safe_httpeex** escapes 5 characters everywhere (unified):
```
& → &amp;    < → &lt;    > → &gt;    " → &quot;    ' → &#39;
```
`escapeAttr()` is just an alias for `escapeHtml()` — same 5 chars for all contexts.

**httpeex-accumulator** has context-specific escaping:
- `HtmlBuilder.append()` escapes: `& < > " '` (5 chars)
- `AttrBuilder.append()` escapes: `& " < >` (4 chars, no single quote)
- `escapeHtmlSafe()` in HtmlSafe escapes: `& < >` only (3 chars)
- `escapeAttrSafe()` in AttrSafe escapes: `& " < >` (4 chars)
- Original `escapeHtml()` escapes: `& < >` (3 chars)
- Original `escapeAttr()` escapes: `& " < >` (4 chars)

That's **4 different escape function implementations** with 3 different character sets. This fragmentation is itself a security concern — `HtmlSafe.fromUnsafe()` only escapes 3 characters, missing `"` and `'`, which can allow attribute breakout.

### 3. Renderer Design Pattern

**safe_httpeex** passes the accumulator through the call tree:
```temper
let renderNode(node: Node, out: SafeHtmlBuilder): Void {
  when (node) {
    is Text -> out.append(node.content);        // escaped by accumulator
    is Element -> renderElement(node, out);      // passes out through
    ...
  }
}
```
One mutable accumulator flows through the entire render. `appendSafe()` for structure, `append()` for user content. Clean and direct.

**httpeex-accumulator** (renderer-safe) returns `HtmlSafe` values and concatenates them:
```temper
let renderNodeSafe(node: Node): HtmlSafe {
  when (node) {
    is Text -> HtmlSafe.fromUnsafe(node.content);
    is Element -> renderElementSafe(node);         // returns HtmlSafe
    ...
  }
}
```
Each function builds a `ListBuilder<HtmlSafe>`, adds parts, then calls `concatAll()` to join them. This creates many intermediate list and string allocations.

### 4. Compile-Time vs Runtime Safety

**safe_httpeex** provides *both*:
- Compile-time: The renderer itself uses `appendSafe`/`append` correctly
- Consumer-facing: Exports `SafeHtmlBuilder` as a tagged string tag, so consumers can write `SafeHtml"<div>${userInput}</div>"` and get compiler-enforced escaping

**httpeex-accumulator** provides *both*, but separately:
- Compile-time: `HtmlBuilder` accumulator (defined but not used by the renderer)
- Runtime: `HtmlSafe`/`AttrSafe` wrappers (used by renderer-safe)
- The compile-time accumulator (`HtmlBuilder`) and the runtime renderer (`renderer-safe` using `HtmlSafe`) are **disconnected** — neither uses the other

### 5. File Organization

**safe_httpeex**: 7 source files — the safety module replaces the original escaping, so the file count stays the same as a non-safe implementation.

**httpeex-accumulator**: 12 source files — adds 5 files on top of the original:
- `html-accumulator.temper.md` (compile-time accumulators)
- `html-safe.temper.md` (runtime type wrappers)
- `renderer-safe.temper.md` (parallel safe renderer)
- `test-simple.temper.md` (accumulator syntax test)
- `test-htmlsafe.temper.md` (runtime safety test)
- `example-generated.temper.md` (code generation example)

---

## Security Analysis

### Unescaped Code Paths

**safe_httpeex**: User content always goes through `append()` → `escapeHtml()`. The only way to emit unescaped content is `appendSafe()`, which is only called with template structure literals. **0 unescaped user content paths.**

**httpeex-accumulator**:
- Original renderer (`renderer.temper.md`): expressions, dynamic attributes, spread attributes, special attributes, EEx code, comments all go through `out.append()` with no escaping. **6+ unescaped paths** (same as original httpeex).
- Safe renderer (`renderer-safe.temper.md`): expressions still use `HtmlSafe.literal(expr.code)` — the `.literal()` constructor bypasses escaping. Comments use `HtmlSafe.literal("<!-- ${comment.content} -->")`. **At least 2 unescaped paths** even in the "safe" renderer.

### Escaping Completeness

| Context | safe_httpeex | accumulator (HtmlBuilder) | accumulator (HtmlSafe) | accumulator (original) |
|---------|-------------|---------------------------|------------------------|----------------------|
| `&` | YES | YES | YES | YES |
| `<` | YES | YES | YES | YES |
| `>` | YES | YES | YES | YES |
| `"` | YES | YES | **NO** | **NO** |
| `'` | YES | YES | **NO** | **NO** |

The `HtmlSafe.fromUnsafe()` function only escapes 3 characters. If used in an attribute context, a single quote or double quote could break out.

---

## Test Coverage

**safe_httpeex**: 80 integration tests covering roundtrip fidelity, XSS prevention (script injection, attribute breakout, comment breakout), character escaping (all 5 chars individually), and structure preservation. Tests run on 3 backends (JS, Python, Lua).

**httpeex-accumulator**: ~48 integration tests (roundtrip + basic), plus 2 small test files for the accumulator pattern and HtmlSafe type. The safe renderer tests are minimal. Tests appear to run on JS.

---

## What httpeex-accumulator Has That safe_httpeex Doesn't

1. **Runtime type wrappers** (HtmlSafe, AttrSafe) — useful if you want to pass safe HTML fragments around as typed values, compose them, store them. safe_httpeex doesn't have this runtime type; it only has the accumulator.

2. **Context-specific attribute escaping** via a dedicated `AttrBuilder` accumulator — safe_httpeex unifies all escaping into one function (which is arguably more secure, since it escapes the superset of all dangerous characters).

3. **The original renderer preserved** — if you need unescaped template output (e.g., for a template-to-template transform), the original renderer is still there.

4. **Extensive documentation files** — README, IMPLEMENTATION_NOTES, SECURITY_ANALYSIS, SOLUTION, COMPARISON, RUNTIME_VS_COMPILETIME, REIMPLEMENTATION_COMPLETE, SUCCESS (8 docs).

## What safe_httpeex Has That httpeex-accumulator Doesn't

1. **Actually integrated safety** — the safe renderer IS the renderer. Not a parallel option.

2. **Exported tagged string type** — consumers get `SafeHtml"..."` for use in their own code.

3. **Complete escaping** — all 5 OWASP characters in all contexts.

4. **More tests** — 80 vs ~48, with dedicated XSS prevention test cases.

5. **Multi-backend verification** — tests pass on JS, Python, and Lua.

6. **Python demo + Django integration example** — shows real-world usage.

---

## Verdict

**safe_httpeex is the more complete and secure implementation.** It makes safety the default, escapes all dangerous characters, and actually integrates the accumulator into the main rendering pipeline. It has more tests, including security-specific ones.

**httpeex-accumulator explores more design options** (runtime types, context-specific builders, preserving the original renderer) but doesn't fully commit to any of them. The safe renderer isn't exported, the HtmlBuilder accumulator isn't used by the renderer, and the HtmlSafe wrapper has incomplete escaping. It's more of a research prototype showing multiple possible approaches.

| Dimension | safe_httpeex | httpeex-accumulator |
|-----------|-------------|---------------------|
| Safety default | YES - only path | NO - opt-in, not exported |
| Escape completeness | 5/5 chars | 3/5 to 5/5 (varies by function) |
| Integration | Fully integrated | Parallel, disconnected |
| Tests | 80 (3 backends) | ~48 (1 backend) |
| Code size | 2,885 lines | 3,401 lines |
| Design approach | Replace the renderer | Add alongside |
| Consumer API | Tagged string exported | Not exported |
