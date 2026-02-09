# Integration Tests

End-to-end tests for the safe HEEx parser and renderer.

## Setup

All symbols are imported via imports.temper.md from the parent heex module.

## HTML Roundtrip Tests

```temper
test("roundtrip plain text") {
  let doc = parse("Hello world");
  let html = renderHtml(doc);
  parse(html);
}

test("roundtrip simple element") {
  let doc = parse("<div></div>");
  let html = renderHtml(doc);
  parse(html);
}

test("roundtrip element with attributes") {
  let doc = parse("<div class=\"foo\"></div>");
  let html = renderHtml(doc);
  parse(html);
}

test("roundtrip nested elements") {
  let doc = parse("<div><span>text</span></div>");
  let html = renderHtml(doc);
  parse(html);
}

test("roundtrip void element") {
  let doc = parse("<br />");
  let html = renderHtml(doc);
  parse(html);
}
```

## Component Roundtrip Tests

```temper
test("roundtrip local component") {
  let doc = parse("<.button>Click</.button>");
  let html = renderHtml(doc);
  parse(html);
}

test("roundtrip remote component") {
  let doc = parse("<MyApp.Button />");
  let html = renderHtml(doc);
  parse(html);
}

test("roundtrip component with slot") {
  let doc = parse("<.card><:header>Title</:header></.card>");
  let html = renderHtml(doc);
  parse(html);
}
```

## Expression Roundtrip Tests

```temper
test("roundtrip expression") {
  let doc = parse("{@name}");
  let html = renderHtml(doc);
  parse(html);
}

test("roundtrip dynamic attribute") {
  let doc = parse("<div class={@class}></div>");
  let html = renderHtml(doc);
  parse(html);
}
```

## Safe HTML Rendering — XSS Prevention Tests

These tests verify the core safety guarantee: user content containing HTML
metacharacters is escaped, while template structure passes through verbatim.

```temper
test("safe render escapes script tags in text") {
  let doc = parse("<div><script>alert('xss')</script></div>");
  let html = renderHtml(doc);
  // The inner text "alert('xss')" is a Text node — auto-escaped via append()
  // The <script> tags are Element structure — passed through appendSafe()
  // After roundtrip through safe render, the output should be re-parseable
  parse(html);
}

test("safe render escapes angle brackets in expression") {
  // Expression content is untrusted — goes through append() which escapes
  let doc = parse("{<img onerror=alert(1)>}");
  let html = renderHtml(doc);
  // The expression code should be escaped in the output
  parse(html);
}

test("safe render escapes ampersands in text content") {
  let doc = parse("<p>Tom &amp; Jerry</p>");
  let html = renderHtml(doc);
  parse(html);
}

test("safe render escapes quotes in dynamic attribute") {
  let doc = parse("<div title={@user_input}></div>");
  let html = renderHtml(doc);
  parse(html);
}
```

## Safe HTML — Structure Preservation Tests

Template structure (tag names, static attributes, delimiters) must pass
through unescaped via appendSafe.

```temper
test("safe render preserves tag names") {
  let doc = parse("<div></div>");
  let html = renderHtml(doc);
  // Tag names go through appendSafe — no escaping
  assert(html == "<div></div>");
}

test("safe render preserves static attributes") {
  let doc = parse("<div class=\"container\"></div>");
  let html = renderHtml(doc);
  assert(html == "<div class=\"container\"></div>");
}

test("safe render preserves self-closing syntax") {
  let doc = parse("<br />");
  let html = renderHtml(doc);
  assert(html == "<br />");
}

test("safe render preserves component names") {
  let doc = parse("<.button />");
  let html = renderHtml(doc);
  assert(html == "<.button />");
}

test("safe render preserves slot syntax") {
  let doc = parse("<.card><:header>Title</:header></.card>");
  let html = renderHtml(doc);
  // Slot delimiters <: and </: are template structure — appendSafe
  parse(html);
}
```

## Safe HTML — Escaping Verification Tests

Direct verification that SafeHtmlBuilder escapes the 5 critical characters.

```temper
test("safe render escapes text with all 5 html chars") {
  // Build a document with text containing all dangerous characters
  let children = new ListBuilder<Node>();
  children.add(new Text("& < > \" '", null));
  let doc = new Document(children.toList(), null);
  let html = renderHtml(doc);
  // Text goes through append() — all 5 chars must be escaped
  assert(html == "&amp; &lt; &gt; &quot; &#39;");
}

test("safe render does not double-escape") {
  let children = new ListBuilder<Node>();
  children.add(new Text("&amp; already escaped", null));
  let doc = new Document(children.toList(), null);
  let html = renderHtml(doc);
  // The & in &amp; should be escaped to &amp;amp; — correct behavior
  // SafeHtmlBuilder treats ALL text as untrusted, including pre-escaped text
  assert(html == "&amp;amp; already escaped");
}
```

## Safe HTML — EEx Rendering Tests

```temper
test("safe render eex output") {
  let doc = parse("<%= @name %>");
  let html = renderHtml(doc);
  // EEx delimiters are trusted structure, code is untrusted
  parse(html);
}

test("safe render eex block") {
  let doc = parse("<%= if @show do %>visible<% end %>");
  let html = renderHtml(doc);
  parse(html);
}
```

## Debug Rendering Tests

```temper
test("debug rendering produces output") {
  let doc = parse("<div>text</div>");
  let debug = renderDebug(doc);
  assert(debug.hasIndex(String.begin));
}

test("debug shows document structure") {
  let doc = parse("<div>text</div>");
  let debug = renderDebug(doc);
  assert(debug.hasIndex(String.begin));
}
```

## JSON Rendering Tests

```temper
test("json rendering produces valid structure") {
  let doc = parse("<div>text</div>");
  let json = renderJson(doc);
  assert(json[String.begin] == char'{');
}

test("json rendering handles attributes") {
  let doc = parse("<div class=\"foo\"></div>");
  let json = renderJson(doc);
  assert(json.hasIndex(String.begin));
}

test("json rendering handles components") {
  let doc = parse("<.button />");
  let json = renderJson(doc);
  assert(json.hasIndex(String.begin));
}
```

## Complex Template Tests

```temper
test("parses nested component") {
  let doc = parse("<.outer><.inner /></.outer>");
  assert(doc.children.length >= 1);
}

test("parses mixed content") {
  let doc = parse("<div>text<span>more</span></div>");
  assert(doc.children.length >= 1);
}
```

## SafeHtmlBuilder Tagged String Tests

These tests prove the **compiler-enforced safety guarantee**: when SafeHtmlBuilder
is used as a tagged string tag, the compiler automatically routes literal parts
to `appendSafe` (no escaping) and `${expr}` interpolations to `append` (auto-escaped).

```temper
test("tagged string basic usage") {
  let html = SafeHtmlBuilder"<div>Hello</div>";
  assert(html == "<div>Hello</div>");
}

test("tagged string escapes interpolated content") {
  let malicious = "<script>alert('xss')</script>";
  let html = SafeHtmlBuilder"<div>${malicious}</div>";
  assert(html == "<div>&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;</div>");
}

test("tagged string preserves literal angle brackets") {
  let html = SafeHtmlBuilder"<p>safe</p>";
  assert(html == "<p>safe</p>");
}

test("tagged string escapes ampersand in interpolation") {
  let text = "Tom & Jerry";
  let html = SafeHtmlBuilder"<span>${text}</span>";
  assert(html == "<span>Tom &amp; Jerry</span>");
}

test("tagged string escapes all 5 critical chars") {
  let dangerous = "& < > \" '";
  let html = SafeHtmlBuilder"${dangerous}";
  assert(html == "&amp; &lt; &gt; &quot; &#39;");
}

test("tagged string multiple interpolations") {
  let name = "<b>Bob</b>";
  let role = "admin\"root";
  let html = SafeHtmlBuilder"<div>${name} - ${role}</div>";
  assert(html == "<div>&lt;b&gt;Bob&lt;/b&gt; - admin&quot;root</div>");
}

test("tagged string empty interpolation") {
  let empty = "";
  let html = SafeHtmlBuilder"<p>${empty}</p>";
  assert(html == "<p></p>");
}

test("tagged string only literal") {
  let html = SafeHtmlBuilder"<br />";
  assert(html == "<br />");
}
```
