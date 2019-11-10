#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
I don't care if this is messy, it fixes a load of annoying caveats with Sphinx documentation generation that have
existed for too long and still are not addressed despite numerous issues.

Modified from:
    https://github.com/sphinx-doc/sphinx/blob/8c946570dc6227c70b690a33320916cb7f9dae9e/sphinx/ext/graphviz.py
    https://github.com/sphinx-doc/sphinx/blob/8c946570dc6227c70b690a33320916cb7f9dae9e/sphinx/ext/inheritance_diagram.py
"""
from typing import cast
from typing import Dict
from typing import Iterable
from typing import Tuple

from docutils import nodes
from sphinx import addnodes
from sphinx.ext import graphviz
from sphinx.ext import inheritance_diagram
from sphinx.ext.graphviz import GraphvizError
from sphinx.ext.graphviz import logger
from sphinx.ext.graphviz import render_dot
from sphinx.ext.inheritance_diagram import get_graph_hash
from sphinx.locale import __
from sphinx.writers.html import HTMLTranslator

EXPECTED_GITLAB_ROUTE = f"https://{author.lower()}.gitlab.io/{project.lower()}/technical"


def render_dot_html(self: HTMLTranslator, node: graphviz, code: str, options: Dict,
                    prefix: str = 'graphviz', imgcls: str = None, alt: str = None
                    ) -> Tuple[str, str]:
    """
    Makes the SVG diagrams clickable to expand them in a new tab for closer reading.
    """
    format = self.builder.config.graphviz_output_format
    try:
        if format not in ('png', 'svg'):
            raise GraphvizError(__("graphviz_output_format must be one of 'png', "
                                   "'svg', but is %r") % format)
        fname, outfn = render_dot(self, code, options, format, prefix)
    except GraphvizError as exc:
        logger.warning(__('dot code %r: %s'), code, exc)
        raise nodes.SkipNode

    if imgcls:
        imgcls += " graphviz"
    else:
        imgcls = "graphviz"

    if fname is None:
        self.body.append(self.encode(code))
    else:
        if alt is None:
            alt = node.get('alt', self.encode(code).strip())
        if 'align' in node:
            self.body.append('<div align="%s" class="align-%s">' %
                             (node['align'], node['align']))

        self.body.append(f"<h2>Inheritance Diagram</h2>")
        self.body.append(f"<p>Click <a href={fname!r}>here</a> to view the full diagram if too small to read!</p>")
        if format == 'svg':
            self.body.append(f'<div class="graphviz" onclick="window.location.href={fname!r};">')
            self.body.append('<object data="%s" type="image/svg+xml" class="%s">\n' %
                             (fname, imgcls))
            self.body.append('<p class="warning">%s</p>' % alt)
            self.body.append('</object></div>\n')
        else:
            self.body.append(f'<div class="graphviz" onclick="window.location.href={fname!r};">')
            self.body.append('<img src="%s" alt="%s" class="%s" />' %
                             (fname, alt, imgcls))
            self.body.append('</div>\n')
        if 'align' in node:
            self.body.append('</div>\n')

    raise nodes.SkipNode


def html_visit_inheritance_diagram(self, node):
    # type: (HTMLTranslator, inheritance_diagram) -> None
    """
    Output the graph for HTML.  This will insert a PNG with clickable
    image map.
    """
    graph = node['graph']

    graph_hash = get_graph_hash(node)
    name = 'inheritance%s' % graph_hash

    # Create a mapping from fully-qualified class names to URLs.
    graphviz_output_format = self.builder.env.config.graphviz_output_format.upper()
    current_filename = self.builder.current_docname + self.builder.out_suffix
    urls = {}
    pending_xrefs = cast(Iterable[addnodes.pending_xref], node)
    for child in pending_xrefs:
        if child.get('refuri') is not None:
            if graphviz_output_format == 'SVG':
                urls[child['reftitle']] = EXPECTED_GITLAB_ROUTE + "/" + child.get('refuri')
            else:
                urls[child['reftitle']] = child.get('refuri')
        elif child.get('refid') is not None:
            if graphviz_output_format == 'SVG':
                urls[child['reftitle']] = EXPECTED_GITLAB_ROUTE + "/" + current_filename.lstrip("/") + '#' \
                                          + child.get('refid')
            else:
                urls[child['reftitle']] = '#' + child.get('refid')

    dotcode = graph.generate_dot(name, urls, env = self.builder.env)
    render_dot_html(self, node, dotcode, {}, 'inheritance', 'inheritance',
                    alt = 'Inheritance diagram of ' + node['content'])
    raise nodes.SkipNode


# Patch the real versions with our fixed versions.
graphviz.render_dot_html = render_dot_html
inheritance_diagram.html_visit_inheritance_diagram = html_visit_inheritance_diagram
