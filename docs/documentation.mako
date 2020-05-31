<%
    import abc
    import enum
    import inspect
    import textwrap
    import typing

    import pdoc

    from pdoc.html_helpers import extract_toc, glimpse, to_html as _to_html, format_git_link

    def link(dobj: pdoc.Doc, *, with_prefixes=False, simple_names=False, css_classes="", name=None, default_type="", dotted=True, anchor=False):
        prefix = ""
        name = name or dobj.name

        if with_prefixes:        
            if isinstance(dobj, pdoc.Function):
                prefix = "<small class='text-muted'><em>" + dobj.funcdef() + " </em></small> "

            elif isinstance(dobj, pdoc.Variable):
                if dobj.module.name == "typing" or dobj.docstring and dobj.docstring.casefold().startswith("type hint"):
                    prefix = "<small class='text-muted'><em>type hint </em></small>"
                elif all(not c.isalpha() or c.isupper() for c in dobj.name):
                    prefix = "<small class='text-muted'><em>const </em></small>"
                else:
                    prefix = "<small class='text-muted'><em>var </em></small>"

            elif isinstance(dobj, pdoc.Class):
                if issubclass(dobj.obj, type):
                    qual = "metaclass"
                else:
                    if enum.Flag in dobj.obj.mro():
                        qual = "enum flag"        
                    elif enum.Enum in dobj.obj.mro():
                        qual = "enum"
                    else:
                        qual = "class"

                    if inspect.isabstract(dobj.obj):
                        qual = "abstract " + qual
            
                prefix = f"<small class='text-muted'><em>{qual} </em></small> "

                if "__call__" in dobj.obj.__dict__:
                    name += "()"

            elif isinstance(dobj, pdoc.Module):
                qual = "package" if dobj.is_package else "namespace" if dobj.is_namespace else "module"
                prefix = f"<small class='text-muted'><em>{qual} </em></small> "

            else:
                prefix = f"<small class='text-muted'><em>{default_type} </em></small>"
        else:
            name = name or dobj.name or ""


        if isinstance(dobj, pdoc.External) and not external_links:
            return name

        url = dobj.url(relative_to=module, link_prefix=link_prefix, top_ancestor=not show_inherited_members)

        if simple_names:
            name = simple_name(name)

        classes = []
        if dotted:
            classes.append("dotted")
        if css_classes:
            classes.append(css_classes)
        class_str = " ".join(classes)

        if class_str.strip():
            class_str = f"class={class_str!r}"

        anchor = "" if not anchor else f'id="{dobj.refname}"'

        return '{} <a title="{}" href="{}" {} {}>{}</a>'.format(prefix, glimpse(dobj.docstring), url, anchor, class_str, name)

    def simple_name(s):
        _, _, name = s.rpartition(".")
        return name

    def get_annotation(bound_method, sep=':'):
        annot = show_type_annotations and bound_method(link=link) or ''
        annot = annot.replace("NoneType", "None")
        # Remove quotes.
        if annot.startswith("'") and annot.endswith("'"):
            annot = annot[1:-1]
        if annot:
            annot = ' ' + sep + '\N{NBSP}' + annot
        return annot

    def to_html(text):
        return _to_html(text, module=module, link=link, latex_math=latex_math)
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
                    <li class="breadcrumb-item">${link(m, with_prefixes=False, simple_names=True)}</li>
                % endif
            % endfor
        </ol>
    </nav>
</%def>

<%def name="show_var(v, is_nested=False)">
    <% return_type = get_annotation(v.type_annotation) %>
    <dt>
        <pre><code class="python">${link(v, anchor=True)}${return_type}</code></pre>
    </dt>
    <dd>${v.docstring | to_html}</dd>
</%def>

<%def name="show_func(f, is_nested=False)">
    <%
        params = f.params(annotate=show_type_annotations, link=link)
        return_type = get_annotation(f.return_annotation, '->')
        example_str = f.funcdef() + f.name + "(" + ", ".join(params) + ")" + return_type

        if len(params) > 4 or len(example_str) > 70:
            representation = "\n".join((
                f.funcdef() + " " + f.name + "(",
                *(f"    {p}," for p in params),
                ")" + return_type + ": ..."
            ))
        else:
            representation = f"{f.funcdef()} {f.name}(){return_type}: ..."
    %>
    <dt>
        <pre><code id="${f.refname}" class="hljs python">${representation}</code></pre>
    </dt>
    <dd>
        ${show_desc(f)}

        ${show_source(f)}
    </dd>
    <div class="sep"></div>

</%def>

<%def name="show_class(c, is_nested=False)">
    <%
        class_vars = c.class_variables(show_inherited_members, sort=sort_identifiers)
        smethods = c.functions(show_inherited_members, sort=sort_identifiers)
        inst_vars = c.instance_variables(show_inherited_members, sort=sort_identifiers)
        methods = c.methods(show_inherited_members, sort=sort_identifiers)
        mro = c.mro()
        subclasses = c.subclasses()

        params = c.params(annotate=show_type_annotations, link=link)
        example_str = "class " + c.name + "(" + ", ".join(params) + ")"

        if len(params) > 4 or len(example_str) > 70:
            representation = "\n".join((
                f"class {c.name} (",
                *(f"    {p}," for p in params),
                "): ..."
            ))
        elif params:
            representation = f"class {c.name} (" + ", ".join(params) + "): ..."
        else:
            representation = f"class {c.name}: ..."
    %>
    <dt>
        <h4>${link(c, with_prefixes=True, simple_names=True)}</h4>
    </dt>
    <dd>
        <pre><code id="${c.refname}" class="hljs python">${representation}</code></pre>

        ${show_desc(c)}
        <div class="sep"></div>

        % if subclasses:
            <h5>Subclasses</h5>
            <dl>
                % for sc in subclasses:
                    <dt class="nested">${link(sc, with_prefixes=True, default_type="class")}</dt>
                    <dd class="nested">${sc.docstring | glimpse, to_html}</dd>
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
                    <dt class="nested">${link(mro_c, with_prefixes=True, default_type="class")}</dt>
                    <dd class="nested">${mro_c.docstring | glimpse, to_html}</dd>
                % endfor
            </dl>
            <div class="sep"></div>
        % endif

        % if class_vars:
            <h5>Class variables</h5>
            <dl>
                % for cv in class_vars:
                    ${show_var(cv)}
                % endfor
            </dl>
            <div class="sep"></div>
        % endif

        % if smethods:
            <h5>Class methods</h5>
            <dl>
                % for m in smethods:
                    ${show_func(m)}
                % endfor
            </dl>
            <div class="sep"></div>
        % endif

        % if inst_vars:
            <h5>Instance variables</h5>
            <dl>
                % for i in inst_vars:
                    ${show_var(i)}
                % endfor
            </dl>
            <div class="sep"></div>
        % endif

        % if methods:
            <h5>Instance methods</h5>
            <dl>
                % for m in methods:
                    ${show_func(m)}
                % endfor
            </dl>
            <div class="sep"></div>
        % endif
    </dd>
</%def>

<%def name="show_desc(d, short=False)">
    
    <%
        inherits = ' inherited' if d.inherits else ''
        # docstring = glimpse(d.docstring) if short or inherits else d.docstring
        docstring = d.docstring
    %>
    % if d.inherits:
        <p class="inheritance">
            <em>Inherited from:</em>
            % if hasattr(d.inherits, 'cls'):
                <code>${link(d.inherits.cls, with_prefixes=False)}</code>.<code>${link(d.inherits, name=d.name, with_prefixes=False)}</code>
            % else:
                <code>${link(d.inherits, with_prefixes=False)}</code>
            % endif
        </p>
    % endif

    ${docstring | to_html}
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
            variables = module.variables(sort=sort_identifiers)
            classes = module.classes(sort=sort_identifiers)
            functions = module.functions(sort=sort_identifiers)
            submodules = module.submodules()
            supermodule = module.supermodule
        %>

        <div class="d-md-none d-lg-block col-lg-5 col-xl-4">
            <nav class="nav flex-column" id="content-nav">
                % if submodules:
                    <ul class="list-unstyled">
                        % for child_module in submodules:
                            <li><code>${link(child_module, with_prefixes=True, css_classes="sidebar-nav-pill", dotted=False)}</code></li>
                        % endfor
                    </ul>
                % endif

                % if variables or functions or classes:
                    <h3>This module</h3>
                % endif

                % if variables:
                    <ul class="list-unstyled">
                        % for variable in variables:
                            <li><code>${link(variable, with_prefixes=True, css_classes="sidebar-nav-pill", dotted=False)}</code></li>
                        % endfor
                    </ul>
                % endif

                % if functions:
                    <ul class="list-unstyled">
                        % for function in functions:
                            <li><code>${link(function, with_prefixes=True, css_classes="sidebar-nav-pill", dotted=False)}</code></li>
                        % endfor
                    </ul>
                % endif

                % if classes:
                    % for c in classes:
                        ## Purposely using one item per list for layout reasons.
                        <ul class="list-unstyled">
                            <li>
                                <code>${link(c, with_prefixes=True, css_classes="sidebar-nav-pill", dotted=False)}</code>

                                <%
                                    members = c.functions(sort=sort_identifiers) + c.methods(sort=sort_identifiers)

                                    if list_class_variables_in_index:
                                        members += (c.instance_variables(sort=sort_identifiers) + c.class_variables(sort=sort_identifiers))
                                    
                                    if not show_inherited_members:
                                        members = [i for i in members if not i.inherits]
                                    
                                    if sort_identifiers:
                                        members = sorted(members)
                                %>

                                <ul class="list-unstyled nested">
                                    % if members:
                                        % for member in members:
                                            <li><code>${link(member, with_prefixes=True, css_classes="sidebar-nav-pill", dotted=False)}</code></li>
                                        % endfor
                                    % endif
                                </ul>

                            </li>
                        </ul>
                    % endfor
                % endif
            </nav>
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