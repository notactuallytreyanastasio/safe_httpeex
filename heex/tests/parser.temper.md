# Parser Tests

Unit tests for the HEEx parser.

## Setup

All symbols are imported via imports.temper.md from the parent heex module.

## Text Parsing

```temper
test("parses plain text") {
  let doc = parse("Hello world");
  assert(doc.children.length == 1);
  let text = doc.children[0] as Text;
  assert(text.content == "Hello world");
}

test("parses empty document") {
  let doc = parse("");
  assert(doc.children.length == 0);
}
```

## Element Parsing

```temper
test("parses simple element") {
  let doc = parse("<div></div>");
  assert(doc.children.length == 1);
  let el = doc.children[0] as Element;
  assert(el.tag == "div");
  assert(el.children.length == 0);
}

test("parses self-closing element") {
  let doc = parse("<br/>");
  let el = doc.children[0] as Element;
  assert(el.tag == "br");
  assert(el.selfClosing);
}

test("parses void element") {
  let doc = parse("<input>");
  let el = doc.children[0] as Element;
  assert(el.tag == "input");
}

test("parses nested elements") {
  let doc = parse("<div><span></span></div>");
  let outer = doc.children[0] as Element;
  assert(outer.tag == "div");
  assert(outer.children.length == 1);
  let inner = outer.children[0] as Element;
  assert(inner.tag == "span");
}

test("parses element with text") {
  let doc = parse("<p>Hello</p>");
  let el = doc.children[0] as Element;
  assert(el.tag == "p");
  assert(el.children.length == 1);
  let text = el.children[0] as Text;
  assert(text.content == "Hello");
}
```

## Attribute Parsing

```temper
test("parses static attribute") {
  let doc = parse("<div class=\"foo\"></div>");
  let el = doc.children[0] as Element;
  assert(el.attributes.length == 1);
  let attr = el.attributes[0] as StaticAttribute;
  assert(attr.name == "class");
  assert(attr.value == "foo");
}

test("parses multiple attributes") {
  let doc = parse("<div id=\"main\" class=\"container\"></div>");
  let el = doc.children[0] as Element;
  assert(el.attributes.length == 2);
}

test("parses dynamic attribute") {
  let doc = parse("<div class={@class}></div>");
  let el = doc.children[0] as Element;
  let attr = el.attributes[0] as DynamicAttribute;
  assert(attr.name == "class");
}

test("parses spread attribute") {
  let doc = parse("<div {@attrs}></div>");
  let el = doc.children[0] as Element;
  let attr = el.attributes[0] as SpreadAttribute;
  assert(attr.expression.code == "@attrs");
}

test("parses special attribute") {
  let doc = parse("<div :if={@show}></div>");
  let el = doc.children[0] as Element;
  let attr = el.attributes[0] as SpecialAttribute;
  assert(attr.kind == "if");
}
```

## Component Parsing

```temper
test("parses local component") {
  let doc = parse("<.button></.button>");
  let comp = doc.children[0] as Component;
  assert(comp.name == ".button");
  assert(comp.componentType.kind == "local");
}

test("parses self-closing component") {
  let doc = parse("<.icon />");
  let comp = doc.children[0] as Component;
  assert(comp.name == ".icon");
}

test("parses remote component") {
  let doc = parse("<MyApp.Button></MyApp.Button>");
  let comp = doc.children[0] as Component;
  assert(comp.name == "MyApp.Button");
  assert(comp.componentType.kind == "remote");
}

test("parses component with children") {
  let doc = parse("<.card>Content</.card>");
  let comp = doc.children[0] as Component;
  assert(comp.children.length == 1);
}
```

## Slot Parsing

```temper
test("parses named slot") {
  let doc = parse("<.card><:header>Title</:header></.card>");
  let comp = doc.children[0] as Component;
  assert(comp.slots.length == 1);
  let slot = comp.slots[0];
  assert(slot.name == "header");
}

test("parses multiple slots") {
  let doc = parse("<.card><:header>Title</:header><:footer>Footer</:footer></.card>");
  let comp = doc.children[0] as Component;
  assert(comp.slots.length == 2);
}
```

## Expression Parsing

```temper
test("parses text with expression") {
  let doc = parse("Hello {@name}");
  assert(doc.children.length == 2);
  let expr = doc.children[1] as Expression;
  assert(expr.code == "@name");
}

test("parses expression in element") {
  let doc = parse("<span>{@value}</span>");
  let el = doc.children[0] as Element;
  assert(el.children.length == 1);
  let expr = el.children[0] as Expression;
  assert(expr.code == "@value");
}
```

## EEx Parsing

```temper
test("parses eex output") {
  let doc = parse("<%= @name %>");
  let eex = doc.children[0] as EEx;
  assert(eex.eexType.kind == "output");
}

test("parses eex eval") {
  let doc = parse("<% x = 1 %>");
  let eex = doc.children[0] as EEx;
  assert(eex.eexType.kind == "exec");
}

test("parses eex comment") {
  let doc = parse("<%# comment %>");
  let eex = doc.children[0] as EEx;
  assert(eex.eexType.kind == "comment");
}

test("parses eex block") {
  let doc = parse("<%= if @show do %>visible<% end %>");
  let block = doc.children[0] as EExBlock;
  assert(block.blockType == "if");
}
```

## Comment Parsing

```temper
test("parses HTML comment") {
  let doc = parse("<!-- comment -->");
  let comment = doc.children[0] as Comment;
  assert(comment.content == " comment ");
}
```
