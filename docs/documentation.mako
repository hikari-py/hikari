<%!
    import os
    import typing
    import builtins
    import importlib
    import inspect
    import re
    import sphobjinv
    import urllib.error

    inventory_urls = [
        "https://docs.python.org/3/objects.inv",
        "https://docs.aiohttp.org/en/stable/objects.inv",
        "https://www.attrs.org/en/stable/objects.inv",
        "https://multidict.readthedocs.io/en/latest/objects.inv",
        "https://yarl.readthedocs.io/en/latest/objects.inv",
    ]

    inventories = {}

    for i in inventory_urls:
        try:
            print("Prefetching", i)
            inv = sphobjinv.Inventory(url=i)
            url, _, _ = i.partition("objects.inv")
            inventories[url] = inv.json_dict()
        except urllib.error.URLError as ex:
            # Ignore not being able to fetch inventory when not on CI
            if "CI" not in os.environ:
                print(f"Not able to prefetch {i}. Will continue without it")
                continue

            raise

    located_external_refs = {}
    unlocatable_external_refs = set()

    def discover_source(fqn):
        if fqn in unlocatable_external_refs:
            return

        if fqn.startswith("builtins."):
            fqn = fqn.replace("builtins.", "")

        if fqn not in located_external_refs:
            # print("attempting to find intersphinx reference for", fqn)
            for base_url, inv in inventories.items():
                for obj in inv.values():
                    if isinstance(obj, dict) and obj["name"] == fqn:
                        uri_frag = obj["uri"]
                        if uri_frag.endswith("$"):
                            uri_frag = uri_frag[:-1] + fqn

                        url = base_url + uri_frag
                        # print("discovered", fqn, "at", url)
                        located_external_refs[fqn] = url
                        break
        try:
            return located_external_refs[fqn]
        except KeyError:
            # print("blacklisting", fqn, "as it cannot be dereferenced from external documentation")
            unlocatable_external_refs.add(fqn)

    project_inventory = sphobjinv.Inventory()

    import atexit

    @atexit.register
    def dump_inventory():
        import hikari

        project_inventory.project = "hikari"
        project_inventory.version = hikari.__version__

        text = project_inventory.data_file(contract=True)
        ztext = sphobjinv.compress(text)
        sphobjinv.writebytes('public/objects.inv', ztext)


    # To get links to work in type hints to builtins, we do a bit of hacky search-replace using regex.
    # This generates regex to match general builtins in typehints.
    builtin_patterns = [
        re.compile(f"(?<!builtins\\.)\\b({obj})\\b")
        for obj in dir(builtins)
    ]


%>
<%
    import abc
    import ast
    import enum
    import functools
    import inspect
    import re
    import textwrap

    import pdoc

    from pdoc.html_helpers import extract_toc, glimpse, to_html as _to_html, format_git_link

    # Hikari Enum hack
    from hikari.internal import enums

    # Allow imports to resolve properly.
    typing.TYPE_CHECKING = True


    QUAL_ABC = "<abbr title='An abstract base class which may have abstract methods and abstract properties.'>abstract</abbr>"
    QUAL_ABSTRACT = "<abbr title='An abstract method or property that must be overridden in a derived class.'>abstract</abbr>"
    QUAL_ASYNC_DEF = "<abbr title='A function that returns a coroutine and must be awaited.'>async def</abbr>"
    QUAL_CLASS = "<abbr title='A standard Python type.'>class</abbr>"
    QUAL_DATACLASS = "<abbr title='A standard Python type that represents some form of information or entity.'>dataclass</abbr>"
    QUAL_CACHED_PROPERTY = "<abbr title='A Python property that caches any result for subsequent re-use.'>cached property</abbr>"
    QUAL_CONST = "<abbr title='A variable that should be considered to be a constant value.'>const</abbr>"
    QUAL_DEF = "<abbr title='A standard Python function.'>def</abbr>"
    QUAL_ENUM = "<abbr title='A standard Python enum type. This contains one or more discrete \"constant\" values.'>enum</abbr>"
    QUAL_ENUM_FLAG = "<abbr title='A Python enum type that supports combination using bitwise flags.'>enum flag</abbr>"
    QUAL_EXCEPTION = "<abbr title='A standard Python Exception that can be raised and caught.'>exception</abbr>"
    QUAL_EXTERNAL = "<abbr title='Anything that is external to this library.'>extern</abbr>"
    QUAL_INTERFACE = "<abbr title='An abstract base class that has EMPTY slots, and only methods/properties. Can safely be used in multiple inheritance without side effects.'>abstract trait</abbr>"
    QUAL_METACLASS = "<abbr title='A standard Python metaclass type.'>meta</abbr>"
    QUAL_MODULE = "<abbr title='A standard Python module.'>module</abbr>"
    QUAL_NAMESPACE = "<abbr title='A standard Python PEP-420 namespace package.'>namespace</abbr>"
    QUAL_PACKAGE = "<abbr title='A standard Python package.'>package</abbr>"
    QUAL_PROPERTY = "<abbr title='A descriptor on an object that behaves like a synthetic attribute/variable.'>property</abbr>"
    QUAL_PROTOCOL = "<abbr title='A structural supertype (similar to an ABC, but with implicit inheritance)'>trait</abbr>"
    QUAL_TYPEHINT = "<abbr title='A type hint that is usable by static-type checkers like MyPy, but otherwise serves no functional purpose.'>type hint</abbr>"
    QUAL_VAR = "<abbr title='A standard variable'>var</abbr>"
    QUAL_WARNING = "<abbr title='A standard Python warning that can be raised.'>warning</abbr>"

    def get_url_for_object_from_imports(name, dobj):
        if dobj.module:
            fqn = dobj.module.obj.__name__ + "." + dobj.obj.__qualname__
        elif hasattr(dobj.obj, "__module__"):
            fqn = dobj.obj.__module__ + "." + dobj.obj.__qualname__
        else:
            fqn = dobj.name

        url = discover_source(fqn)
        if url is None:
            url = discover_source(name)

        if url is None:
            url = get_url_from_imports(fqn)

        return url

    def get_url_from_imports(fqn):
        if fqn_match := re.match(r"([a-z_]+)\.((?:[^\.]|^\s)+)", fqn):
            if import_match := re.search(f"from (.*) import (.*) as {fqn_match.group(1)}", module.source):
                old_fqn = fqn
                fqn = import_match.group(1) + "." + import_match.group(2) + "." + fqn_match.group(2)
                try:
                    return pdoc._global_context[fqn].url(relative_to=module, link_prefix=link_prefix, top_ancestor=not show_inherited_members)
                    # print(old_fqn, "->", fqn, "via", url)
                except KeyError:
                    # print("maybe", fqn, "is external but aliased?")
                    return discover_source(fqn)
            elif import_match := re.search(f"from (.*) import {fqn_match.group(1)}", module.source):
                old_fqn = fqn
                fqn = import_match.group(1) + "." + fqn_match.group(1) + "." + fqn_match.group(2)
                try:
                    return pdoc._global_context[fqn].url(relative_to=module, link_prefix=link_prefix, top_ancestor=not show_inherited_members)
                    # print(old_fqn, "->", fqn, "via", url)
                except KeyError:
                    # print("maybe", fqn, "is external but aliased?")
                    return discover_source(fqn)
            elif import_match := re.search(f"import (.*) as {fqn_match.group(1)}", module.source):
                old_fqn = fqn
                fqn = import_match.group(1) + "." + fqn_match.group(2)
                try:
                    return pdoc._global_context[fqn].url(relative_to=module, link_prefix=link_prefix, top_ancestor=not show_inherited_members)
                    # print(old_fqn, "->", fqn, "via", url)
                except KeyError:
                    # print("maybe", fqn, "is external but aliased?")
                    return discover_source(fqn)
            else:
                return None

    def get_url_to_object_maybe_module(dobj):
        try:
            # ref = dobj if not hasattr(dobj.obj, "__module__") else pdoc._global_context[dobj.obj.__module__ + "." + dobj.obj.__qualname__]
            ref = pdoc._global_context[dobj.obj.__module__ + "." + dobj.obj.__qualname__]
            return ref.url(relative_to=module, link_prefix=link_prefix, top_ancestor=not show_inherited_members)
        except Exception:
            return dobj.url(relative_to=module, link_prefix=link_prefix, top_ancestor=not show_inherited_members)

    def debuiltinify(phrase: str):
        if phrase.startswith("builtins."):
            phrase = phrase[len("builtins."):]
        elif phrase.startswith("typing."):
            phrase = phrase[len("typing."):]
        elif phrase.startswith("asyncio."):
            phrase = phrase[len("asyncio."):]
        return phrase

    # Fixed Linkify that works with nested type hints...
    def _fixed_linkify(match: typing.Match, *, link: typing.Callable[..., str], module: pdoc.Module, wrap_code=False):
        #print("matched", match.groups(), match.group())

        try:
            code_span = match.group('code')
        except IndexError:
            code_span = match.group()

        if code_span.startswith("`") and code_span.endswith("`"):
            code_span = codespan[1:-1]

        try:
            # If it doesn't parse, it isn't a valid reference.
            ast.parse(code_span)

            # Extract identifiers.
            items = list(re.finditer(r"(\w|\.)+", code_span))[::-1]

            # For each identifier, replace it with a link.
            for match in items:
                phrase = match.group()

                ident = module.find_ident(phrase)

                if isinstance(ident, pdoc.External):
                    phrase = debuiltinify(ident.name)

                    url = get_url_for_object_from_imports(phrase, ident)

                    if url is None:
                        module_part = module.find_ident(phrase.split('.')[0])
                        if not isinstance(module_part, pdoc.External):
                            print(f"Code reference `{phrase}` in module '{module.refname}' does not match any documented object.")
                            print("Type", module_part.__class__, module_part)

                        bits = ident.name.split(".")[:-1]

                        while bits:
                            partial_phrase = ".".join(bits)
                            if partial_phrase in pdoc._global_context:
                                url = pdoc._global_context[partial_phrase].url(relative_to=module, link_prefix=link_prefix, top_ancestor=not show_inherited_members)
                                a_tag = f"<a href={url!r}>{repr(phrase)[1:-1]}</a>"
                                break

                            bits = bits[:-1]
                        else:
                            a_tag = phrase
                    else:
                        a_tag = f"<a href={url!r}>{repr(phrase)[1:-1]}</a>"


                else:
                    url = ident.url(relative_to=module, link_prefix=link_prefix, top_ancestor=not show_inherited_members)
                    a_tag = f"<a href={url!r}>{repr(ident.name)[1:-1]}</a>"

                chunk = slice(*match.span())
                code_span = "".join((
                    code_span[:chunk.start],
                    a_tag,
                    code_span[chunk.stop:],
                ))

            if wrap_code:
                code_span = code_span.replace('[', '\\[')


        except SyntaxError:
            """Raised if it wasn't a valid piece of Python that was given.

            This can happen with `builtins.True`, `builtins.False` or
            `builtins.None`
            """
            if code_span.startswith("builtins."):
                phrase = debuiltinify(code_span)
                url = discover_source(code_span)
                code_span = f"<a href={url!r}>{repr(phrase)[1:-1]}</a>"


        if wrap_code:
            # Wrapping in HTML <code> as opposed to backticks evaluates markdown */_ markers,
            # so let's escape them in text (but not in HTML tag attributes).
            # Backticks also cannot be used because html returned from `link()`
            # would then become escaped.
            # This finds overlapping matches, https://stackoverflow.com/a/5616910/1090455
            cleaned = re.sub(r'(_(?=[^>]*?(?:<|$)))', r'\\\1', code_span)
            return '<code>{}</code>'.format(cleaned)
        return code_span


    from pdoc import html_helpers
    html_helpers._linkify = _fixed_linkify

    # Help, it is a monster!
    def link(
        dobj: pdoc.Doc,
        *,
        with_prefixes=False,
        simple_names=False,
        css_classes="",
        name=None,
        default_type="",
        dotted=True,
        anchor=False,
        fully_qualified=False,
        hide_ref=False,
        recurse=True,
    ):
        prefix = ""
        name = name or dobj.name

        name = debuiltinify(name)

        show_object = False
        if with_prefixes:
            if isinstance(dobj, pdoc.Function):
                qual = QUAL_ASYNC_DEF if dobj._is_async else QUAL_DEF

                if not simple_names:
                    if getattr(dobj.obj, "__isabstractmethod__", False):
                        prefix = f"{QUAL_ABSTRACT} "

                prefix = "<small class='text-muted'><em>" + prefix + qual + "</em></small> "

            elif isinstance(dobj, pdoc.Variable):
                if getattr(dobj.obj, "__isabstractmethod__", False) and not simple_names:
                    prefix = f"{QUAL_ABSTRACT} "

                descriptor = None
                is_descriptor = False

                if hasattr(dobj.cls, "obj"):
                    for cls in dobj.cls.obj.mro():
                        if (descriptor := cls.__dict__.get(dobj.name)) is not None:
                            is_descriptor = hasattr(descriptor, "__get__")
                            break

                if all(not c.isalpha() or c.isupper() for c in dobj.name):
                    prefix = f"<small class='text-muted'><em>{prefix}{QUAL_CONST}</em></small> "
                elif is_descriptor:
                    qual = QUAL_CACHED_PROPERTY if isinstance(descriptor, functools.cached_property) else QUAL_PROPERTY
                    prefix = f"<small class='text-muted'><em>{prefix}{qual}</em></small> "
                elif dobj.module.name == "typing" or dobj.docstring and dobj.docstring.casefold().startswith(("type hint", "typehint", "type alias")):
                    show_object = not simple_names
                    prefix = f"<small class='text-muted'><em>{prefix}{QUAL_TYPEHINT} </em></small> "
                else:
                    prefix = f"<small class='text-muted'><em>{prefix}{QUAL_VAR}</em></small> "

            elif isinstance(dobj, pdoc.Class):
                qual = ""

                if getattr(dobj.obj, "_is_protocol", False):
                    qual += QUAL_PROTOCOL
                elif issubclass(dobj.obj, type):
                    qual += QUAL_METACLASS
                else:
                    if enums.Flag in dobj.obj.mro() or enum.Flag in dobj.obj.mro():
                        qual += QUAL_ENUM_FLAG
                    elif enums.Enum in dobj.obj.mro() or enum.Enum in dobj.obj.mro():
                        qual += QUAL_ENUM
                    elif hasattr(dobj.obj, "__attrs_attrs__"):
                        qual += QUAL_DATACLASS
                    elif issubclass(dobj.obj, Warning):
                        qual += QUAL_WARNING
                    elif issubclass(dobj.obj, BaseException):
                        qual += QUAL_EXCEPTION
                    else:
                        qual += QUAL_CLASS

                    if not simple_names:
                        if inspect.isabstract(dobj.obj):
                            if re.match(r"^I[A-Za-z]", dobj.name):
                                qual = f"{QUAL_INTERFACE} {qual}"
                            else:
                                qual = f"{QUAL_ABC} {qual}"

                prefix = f"<small class='text-muted'><em>{qual}</em></small> "

            elif isinstance(dobj, pdoc.Module):
                qual = QUAL_PACKAGE if dobj.is_package else QUAL_NAMESPACE if dobj.is_namespace else QUAL_MODULE
                prefix = f"<small class='text-muted'><em>{qual}</em></small> "

            else:
                if isinstance(dobj, pdoc.External):
                    prefix = f"<small class='text-muted'><em>{QUAL_EXTERNAL} {default_type}</em></small> "
                else:
                    prefix = f"<small class='text-muted'><em>{default_type}</em></small> "
        else:
            name = name or dobj.name or ""

        if fully_qualified and not simple_names:
            name = dobj.module.name + "." + dobj.obj.__qualname__

        if isinstance(dobj, pdoc.External):
            url = get_url_for_object_from_imports(name, dobj)

            if url is None:
                # print("Could not resolve where", fqn, "came from :(")
                return name
        else:
            url = get_url_to_object_maybe_module(dobj)

        if simple_names:
            name = simple_name(name)

        extra = ""
        if show_object:
            extra = f" = {dobj.obj}"

        classes = []
        class_str = " ".join(classes)

        if class_str.strip():
            class_str = f"class={class_str!r}"

        anchor = "" if not anchor else f'id="{dobj.refname}"'

        return '{}<a title="{}" href="{}" {} {}>{}</a>{}'.format(prefix, dobj.name + " -- " + glimpse(dobj.docstring), url, anchor, class_str, name, extra)

    def simple_name(s):
        _, _, name = s.rpartition(".")
        return name

    def get_annotation(bound_method, sep=':'):
        annot = bound_method(link=link)

        annot = annot.replace("NoneType", "None")
        # Remove quotes.
        if annot.startswith("'") and annot.endswith("'"):
            annot = annot[1:-1]

        if annot.startswith("builtins."):
            annot = annot[len("builtins."):]

        if annot:
            annot = ' ' + sep + '\N{NBSP}' + annot

        # for pattern in builtin_patterns:
        #    annot = pattern.sub(r"builtins.\1", annot)

        return annot

    def to_html(text):
        text = _to_html(text, module=module, link=link, latex_math=latex_math)
        replacements = [
            ('class="admonition info"', 'class="alert alert-primary"'),
            ('class="admonition warning"', 'class="alert alert-warning"'),
            ('class="admonition danger"', 'class="alert alert-danger"'),
            ('class="admonition note"', 'class="alert alert-success"')
        ]

        for before, after in replacements:
            text = text.replace(before, after)

        return text
%>

<%def name="ident(name)"><span class="ident">${name}</span></%def>

<%def name="breadcrumb()">
    <%
        module_breadcrumb = []

        sm = module
        while sm is not None:
            module_breadcrumb.append(sm)
            sm = sm.supermodule

        module_breadcrumb.reverse()
    %>

    <nav aria-label="breadcrumb">
        <ol class="breadcrumb module-breadcrumb">
            % for m in module_breadcrumb:
                % if m is module:
                    <li class="breadcrumb-item active"><a href="#">${m.name | simple_name}</a></li>
                % else:
                    <% url = link(m) %>
                    <li class="breadcrumb-item inactive">${link(m, with_prefixes=False, simple_names=True)}</li>
                % endif
            % endfor
        </ol>
    </nav>
</%def>

<%def name="show_var(v, is_nested=False)">
    <%
        return_type = get_annotation(v.type_annotation)
        parent = v.cls.obj if v.cls is not None else v.module.obj
        if return_type == "":

            if hasattr(parent, "mro"):
                for cls in parent.mro():
                    if hasattr(cls, "__annotations__") and v.name in cls.__annotations__:
                        return_type = get_annotation(lambda *_, **__: cls.__annotations__[v.name])
                        if return_type != "":
                            break

            if hasattr(parent, "__annotations__") and v.name in parent.__annotations__:
                return_type = get_annotation(lambda *_, **__: parent.__annotations__[v.name])

            return_type = re.sub(r'[\w\.]+', functools.partial(_fixed_linkify, link=link, module=v.module), return_type)

        value = None
        if v.cls is not None:
            try:
                obj = getattr(v.cls.obj, v.name)

                simple_bases = (
                    bytes, int, bool, str, float, complex, list, set, frozenset, dict, tuple, type(None),
                    enum.Enum, typing.Container
                )

                if isinstance(obj, simple_bases):
                    value = str(obj)

                    # Combined enum tidyup
                    if value.count("|") > 3 and isinstance(obj, enum.Enum):
                        start = "\n\N{EM SPACE}\N{EM SPACE}\N{EM SPACE}"
                        value = f"({start}   " + f"{start} | ".join(value.split(" | ")) + "\n)"

            except Exception as ex:
                print(v.name, type(ex).__name__, ex)

        if value:
            for enum_mapping in ("_value2member_map_", "_value_to_member_map_"):
                if mapping := getattr(v.cls.obj, enum_mapping, None):
                    try:
                        real_value = getattr(v.cls.obj, v.name)
                        if real_value in mapping.values():
                            return_type += f" = {real_value.value!r}"
                            break
                    except AttributeError:
                        pass
            else:
                return_type += f" = {value}"

        if hasattr(parent, "mro"):
            name = f"{parent.__module__}.{parent.__qualname__}.{v.name}"
        else:
            name = f"{parent.__name__}.{v.qualname}"

        project_inventory.objects.append(
            sphobjinv.DataObjStr(
                name = name,
                domain = "py",
                role = "var",
                uri = v.url(),
                priority = "1",
                dispname = "-",
            )
        )
    %>
    <dt>
        <pre><code class="python">${link(v, with_prefixes=True, anchor=True)}${return_type}</code></pre>
    </dt>
    <dd>${v.docstring | to_html}</dd>
</%def>

<%def name="show_func(f, is_nested=False)">
    <%
        params = f.params(annotate=show_type_annotations, link=link)
        return_type = get_annotation(f.return_annotation, '->')
        qual = QUAL_ASYNC_DEF if f._is_async else QUAL_DEF
        anchored_name = f'<a title="{f.name}" href="{get_url_to_object_maybe_module(f)}" id="{f.refname}">{f.name}</a>'

        example_str = qual + f.name + "(" + ", ".join(params) + ")" + return_type

        if params and params[0] in ("self", "mcs", "mcls", "metacls"):
            params = params[1:]

        if len(params) > 4 or len(params) > 0 and len(example_str) > 70:
            representation = "\n".join((
                qual + " " + anchored_name + "(",
                *(f"    {p}," for p in params),
                ")" + return_type + ": ..."
            ))

        elif params:
            representation = f"{qual} {anchored_name}({', '.join(params)}){return_type}: ..."
        else:
            representation = f"{qual} {anchored_name}(){return_type}: ..."

        if f.module.name != f.obj.__module__:
            try:
                ref = pdoc._global_context[f.obj.__module__ + "." + f.obj.__qualname__]
                redirect = True
            except KeyError:
                redirect = False
        else:
            redirect = False

        if not redirect:
            project_inventory.objects.append(
                sphobjinv.DataObjStr(
                    name = f.obj.__module__ + "." + f.obj.__qualname__,
                    domain = "py",
                    role = "func",
                    uri = f.url(),
                    priority = "1",
                    dispname = "-",
                )
            )
    %>
    <dt>
        <pre><code id="${f.refname}" class="hljs python">${representation}</code></pre>
    </dt>
    <dd>
        % if inspect.isabstract(f.obj):
            <strong>This function is abstract!</strong>
        % endif
        % if redirect:
            ${show_desc(f, short=True)}
            <strong>This function is defined explicitly at ${link(ref, with_prefixes=False, fully_qualified=True)}. Visit that link to view the full documentation!</strong>
        % else:
            ${show_desc(f)}

            ${show_source(f)}
        % endif
    </dd>
    <div class="sep"></div>

</%def>

<%def name="show_class(c, is_nested=False)">
    <%
        variables = c.instance_variables(show_inherited_members, sort=sort_identifiers) + c.class_variables(show_inherited_members, sort=sort_identifiers)
        methods = c.methods(show_inherited_members, sort=sort_identifiers) + c.functions(show_inherited_members, sort=sort_identifiers)
        mro = c.mro()
        subclasses = c.subclasses()

        # No clue why I need to do this, and I don't care at this point. This hurts my brain.
        params = [p.replace("builtins.", "") for p in c.params(annotate=show_type_annotations, link=link)]

        example_str = f"{QUAL_CLASS} " + c.name + "(" + ", ".join(params) + ")"

        suppress_params = getattr(c.obj, "_is_protocol", False)

        if not suppress_params and (len(params) > 4 or len(example_str) > 70 and len(params) > 0):
            representation = "\n".join((
                f"{QUAL_CLASS} {c.name} (",
                *(f"    {p}," for p in params),
                "): ..."
            ))
        elif params and not suppress_params:
            representation = f"{QUAL_CLASS} {c.name} (" + ", ".join(params) + "): ..."
        else:
            representation = f"{QUAL_CLASS} {c.name}: ..."

        if c.module.name != c.obj.__module__:
            try:
                ref = pdoc._global_context[c.obj.__module__ + "." + c.obj.__qualname__]
                redirect = True
            except KeyError:
                redirect = False
        else:
            redirect = False

        if not redirect:
            project_inventory.objects.append(
                sphobjinv.DataObjStr(
                    name = c.obj.__module__ + "." + c.obj.__qualname__,
                    domain = "py",
                    role = "class",
                    uri = c.url(),
                    priority = "1",
                    dispname = "-",
                )
            )
    %>
    <dt>
        % if redirect:
            <h4 id="${c.refname}"><small class='text-muted'>reference to </small>${link(c, with_prefixes=True)}</h4>
        % else:
            <h4>${link(c, with_prefixes=True, simple_names=True)}</h4>
        % endif
    </dt>
    <dd>
        % if redirect:
            <small>${show_desc(c, short=True)}</small>
        % else:
            <pre><code id="${c.refname}" class="hljs python">${representation}</code></pre>

            ${show_desc(c)}
            <div class="sep"></div>
            ${show_source(c)}
            <div class="sep"></div>

            % if subclasses:
                <h5>Subclasses</h5>
                <dl>
                    % for sc in subclasses:
                        % if not isinstance(sc, pdoc.External):
                            <dt class="nested">${link(sc, with_prefixes=True, default_type="class")}</dt>
                            <dd class="nested">${sc.docstring or sc.obj.__doc__ | glimpse, to_html}</dd>
                        % endif
                    % endfor
                </dl>
                <div class="sep"></div>
            % endif

            % if mro:
                <h5>Method resolution order</h5>
                <dl>
                    <dt class="nested">${link(c, with_prefixes=True)}</dt>
                    <dd class="nested"><em class="text-muted">That's this class!</em></dd>
                    % for mro_c in mro:
                        <%
                            if mro_c.obj is None:
                                module, _, cls = mro_c.qualname.rpartition(".")
                                try:
                                    cls = getattr(importlib.import_module(module), cls)
                                    mro_c.docstring = cls.__doc__ or ""
                                except:
                                    pass
                        %>

                        <dt class="nested">${link(mro_c, with_prefixes=True, default_type="class")}</dt>
                        <dd class="nested">${mro_c.docstring | glimpse, to_html}</dd>
                    % endfor
                </dl>
                <div class="sep"></div>
            % endif

            % if variables:
                <h5>Variables and properties</h5>
                <dl>
                    % for i in variables:
                        ${show_var(i)}
                    % endfor
                </dl>
                <div class="sep"></div>
            % endif

            % if methods:
                <h5>Methods</h5>
                <dl>
                    % for m in methods:
                        ${show_func(m)}
                    % endfor
                </dl>
                <div class="sep"></div>
            % endif
        % endif
    </dd>
</%def>

<%def name="show_desc(d, short=False)">
    <%
        inherits = ' inherited' if d.inherits else ''
        docstring = d.docstring or d.obj.__doc__
    %>
    % if not short:
        % if d.inherits:
            <p class="inheritance">
                <em><small>Inherited from:</small></em>
                % if hasattr(d.inherits, 'cls'):
                    <code>${link(d.inherits.cls, with_prefixes=False)}</code>.<code>${link(d.inherits, name=d.name, with_prefixes=False)}</code>
                % else:
                    <code>${link(d.inherits, with_prefixes=False)}</code>
                % endif
            </p>
        % endif

        ${docstring | to_html}
    % else:
        ${docstring | glimpse, to_html}
    % endif
</%def>

<%def name="show_source(d)">
    % if (show_source_code or git_link_template) and d.source and d.obj is not getattr(d.inherits, 'obj', None):
        <% git_link = format_git_link(git_link_template, d) %>
        % if show_source_code:
            <details class="source">
                <summary>
                    <span>Expand source code</span>
                    % if git_link:
                        <br />
                        <a href="${git_link}" class="git-link dotted">Browse git</a>
                    %endif
                </summary>
                <pre><code class="python">${d.source | h}</code></pre>
            </details>
        % elif git_link:
            <div class="git-link-div"><a href="${git_link}" class="git-link dotted">Browse git</a></div>
        %endif
    %endif
</%def>

<div class="jumbotron jumbotron-fluid">
    <div class="container">
        <h1 class="display-4"><code>${breadcrumb()}</code></h1>
        <p class="lead">${module.docstring | to_html}</p>
    </div>
</div>

<div class="container-xl">
    <div class="row">
        <%
            variables = module.variables(sort=sort_identifiers and module.name != "hikari")
            classes = module.classes(sort=sort_identifiers and module.name != "hikari")
            functions = module.functions(sort=sort_identifiers and module.name != "hikari")
            submodules = module.submodules()
            supermodule = module.supermodule

            project_inventory.objects.append(
                sphobjinv.DataObjStr(
                    name = module.name,
                    domain = "py",
                    role = "module",
                    uri = module.url(),
                    priority = "1",
                    dispname = "-",
                )
            )
        %>

        <div class="d-md-none d-lg-block col-lg-5 col-xl-4">
            <!--<nav class="nav" id="content-nav">-->
                % if submodules:
                    <ul class="list-unstyled text-truncate">
                        % for child_module in submodules:
                            <li class="text-truncate monospaced">${link(child_module, with_prefixes=True, css_classes="sidebar-nav-pill", dotted=False, simple_names=True)}</li>
                        % endfor
                    </ul>
                % endif

                % if variables or functions or classes:
                    <h3>This module</h3>
                % endif

                % if variables:
                    <ul class="list-unstyled text-truncate">
                        % for variable in variables:
                            <li class="text-truncate monospaced">${link(variable, with_prefixes=True, css_classes="sidebar-nav-pill", dotted=False, simple_names=True)}</li>
                        % endfor
                    </ul>
                % endif

                % if functions:
                    <ul class="list-unstyled text-truncate">
                        % for function in functions:
                            <li class="text-truncate monospaced">${link(function, with_prefixes=True, css_classes="sidebar-nav-pill", dotted=False, simple_names=True)}</li>
                        % endfor
                    </ul>
                % endif

                % if classes:
                    <ul class="list-unstyled text-truncate">
                        % for c in classes:
                            <%
                                if c.module.name != c.obj.__module__:
                                    try:
                                        ref = pdoc._global_context[c.obj.__module__ + "." + c.obj.__qualname__]
                                        redirect = True
                                    except KeyError:
                                        redirect = False
                                else:
                                    redirect = False

                                members = c.functions(sort=sort_identifiers) + c.methods(sort=sort_identifiers)

                                if list_class_variables_in_index:
                                    members += (c.instance_variables(sort=sort_identifiers) + c.class_variables(sort=sort_identifiers))

                                if not show_inherited_members:
                                    members = [i for i in members if not i.inherits]

                                if sort_identifiers:
                                    members = sorted(members)
                            %>

                            ## Purposely using one item per list for layout reasons.
                            <li class="monospaced">
                                ${link(c, with_prefixes=True, css_classes="sidebar-nav-pill", dotted=False, simple_names=True)}

                                <ul class="list-unstyled nested text-truncate">
                                    % if members and not redirect:
                                        % for member in members:
                                            <li class="text-truncate monospaced">
                                                ${link(member, with_prefixes=True, css_classes="sidebar-nav-pill", dotted=False, simple_names=True)}
                                            </li>
                                        % endfor
                                    % endif
                                    <br />
                                </ul>
                            </li>
                        % endfor
                    </ul>
                % endif
            <!--</nav>-->
        </div>

        <div class="col-xs-12 col-lg-7 col-xl-8">
            <div class="row">
                <div class="col module-source">
                    ${show_source(module)}
                </div>
            </div>


            % if submodules:
                <h2 id="child-modules-heading">Child Modules</h2>
                <section class="definition">
                    <dl classes="no-nest root">
                        % for m in submodules:
                            <dt>${link(m, simple_names=True, with_prefixes=True, anchor=True)}</dt>
                            <dd>${m.docstring | glimpse, to_html}</dd>
                        % endfor
                    </dl>
                </section>
            % endif

            % if variables:
                <h2 id="variables-heading">Variables and Type Hints</h2>
                <section class="definition">
                    <dl class="no-nest root">
                        % for v in variables:
                            ${show_var(v)}
                        % endfor
                    </dl>
                </section>
            % endif

            % if functions:
                <h2 id="functions-heading">Functions</h2>
                <section class="definition">
                    <dl class="no-nest root">
                        % for f in functions:
                            ${show_func(f)}
                        % endfor
                    </dl>
                </section>
            % endif

            % if classes:
                <h2 id="class-heading">Classes</h2>
                <section class="definition">
                    <dl class="no-nest root">
                        % for c in classes:
                            ${show_class(c)}
                        % endfor
                    </dl>
                </section>
            % endif
        </div>
    </div>
</div>
