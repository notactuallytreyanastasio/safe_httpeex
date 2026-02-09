# Temper Compiler Rust Backend Codegen Bug

## Context

We built a Temper project (safe_httpeex) that compiles and passes all 72 tests on JS, Python, and Lua backends, but fails to compile on Rust with 13 errors. The errors are all in generated Rust code, not in our Temper source.

## The Bug

There are two related Rust codegen issues, both triggered by the pattern of using a mutable variable (`var`) inside loops that are inside `when` blocks or method bodies:

### Issue 1: E0434 — Can't capture dynamic environment in a fn item (7 occurrences)

The Temper compiler generates Rust `fn` items that reference local mutable variables from an enclosing scope. Rust requires closures (`|| { ... }`) for capturing outer variables, not bare `fn` items.

Example from generated code (temper.out/rust/safe-heex/src/mod.rs):
```rust
// Line 4357
first__929 = false;  // ERROR: can't capture dynamic environment in a fn item
```

### Issue 2: E0308 — Type mismatch on mutable bool variables (6 occurrences)

The Temper compiler wraps mutable variables in `Arc<RwLock<T>>` for the Rust backend, but in certain contexts (inside `when`/pattern-match branches), the generated code accesses the variable as a bare `bool` instead of going through the `read_locked` accessor properly.

Example from generated code:
```rust
// Line 4354
if ! temper_core::read_locked( & self.first__929) {
//                               ^^^^^^^^^^^^^^^^^ expected `&Arc<RwLock<bool>>`, found `&bool`
```

## The Triggering Temper Pattern

The minimal Temper pattern that triggers this is a mutable `var` used inside a `for` loop within a method, particularly when combined with `when` pattern matching. Here is the actual code from our renderer.temper.md that triggers it:

```temper
let renderJsonNode(node: Node, out: StringBuilder): Void {
  when (node) {
    is Element -> do {
      // ... setup ...
      var first = true;
      for (let attr of node.attributes) {
        if (!first) { out.append(","); }
        first = false;           // <-- This triggers both E0434 and E0308
        renderJsonAttr(attr, out);
      }
      // ...
    };
    // other branches with same pattern
  }
}
```

## Minimal Reproduction Program

Save as `heex/config.temper.md` in a fresh Temper project:

```temper
export let name = "rust-bug-repro";
export let version = "0.1.0";
import(".");
```

Save as `heex/repro.temper.md`:

```temper
interface Item {
  label(): String;
}

class FooItem(public name: String) extends Item {
  public label(): String { name }
}

class BarItem(public value: Int) extends Item {
  public label(): String { "${value}" }
}

export let renderItems(items: List<Item>): String {
  let out = new StringBuilder();
  out.append("[");
  var first = true;
  for (let item of items) {
    if (!first) { out.append(", "); }
    first = false;
    when (item) {
      is FooItem -> out.append(item.name);
      is BarItem -> do {
        out.append("bar:");
        out.append("${item.value}");
      };
      else -> out.append("?");
    }
  }
  out.append("]");
  out.toString()
}
```

Build with:
```bash
JAVA_HOME=/opt/homebrew/opt/openjdk@21 temper build -b rust
```

This should compile fine on JS/Python/Lua but produce Rust compilation errors around the `first = false` line.

## Environment

- Temper: 0.6.1-dev+48-gdb43268 (newer toolchain with tagged string support)
- Rust: stable (tested on macOS ARM64)
- Backends that work: JS, Python, Lua (all 72/72 tests pass)
- Backend with codegen bug: Rust (13 compile errors)
- Backend with separate bug: C# (Newline codegen issue)
- Backend not tested: Java (mvn not installed)

## Workaround

None known at the Temper source level -- the pattern is idiomatic and correct. The bug is in the Temper-to-Rust code generator. The code works correctly on all other backends.

## Impact

This blocks Rust backend support for any Temper code that uses mutable variables inside `for` loops combined with `when` pattern matching -- a common pattern for generating comma-separated output.
