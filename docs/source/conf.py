#!/usr/bin/env python3
"""
Sphinx documentation configuration.
"""
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

import sphinx_bootstrap_theme

import hikari


# -- Project information -----------------------------------------------------

project = hikari.__name__
copyright = hikari.__copyright__
author = hikari.__author__


# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinxcontrib.asyncio',
    'sphinx.ext.autodoc',
    'sphinx_autodoc_typehints'
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = 'bootstrap'
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()
html_static_path = ['_static']

# Theme options are theme-specific and customize the look and feel of a
# theme further.
html_theme_options = {
    # Navigation bar title. (Default: ``project`` value)
    # 'navbar_title': "",

    # Tab name for entire site. (Default: "Site")
    'navbar_site_name': "Docs",

    # A list of tuples containing pages or urls to link to.
    # Valid tuples should be in the following forms:
    #    (name, page)                 # a link to a page
    #    (name, "/aa/bb", 1)          # a link to an arbitrary relative url
    #    (name, "http://example.com", True) # arbitrary absolute url
    # Note the "1" or "True" value above as the third argument to indicate
    # an arbitrary url.
    'navbar_links': [
        ("Source", "http://gitlab.com/nekoka.tt/hikari", True),
        ("Wiki", "http://gitlab.com/nekoka.tt/hikari/wikis", True),
        ("CI", "http://gitlab.com/nekoka.tt/hikari/pipelines", True),
    ],

    # Render the next and previous page links in navbar. (Default: true)
    'navbar_sidebarrel': False,

    # Render the current pages TOC in the navbar. (Default: true)
    'navbar_pagenav': True,

    # Tab name for the current pages TOC. (Default: "Page")
    'navbar_pagenav_name': "This page",

    # Global TOC depth for "site" navbar tab. (Default: 1)
    # Switching to -1 shows all levels.
    'globaltoc_depth': 3,

    # Include hidden TOCs in Site navbar?
    #
    # Note: If this is "false", you cannot have mixed ``:hidden:`` and
    # non-hidden ``toctree`` directives in the same page, or else the build
    # will break.
    #
    # Values: "true" (default) or "false"
    'globaltoc_includehidden': "true",

    # HTML navbar class (Default: "navbar") to attach to <div> element.
    # For black navbar, do "navbar navbar-inverse"
    'navbar_class': "navbar navbar-inverse",

    # Fix navigation bar to top of page?
    # Values: "true" (default) or "false"
    'navbar_fixed_top': "false",

    # Location of link to source.
    # Options are "nav" (default), "footer" or anything else to exclude.
    'source_link_position': "footer",

    # Bootswatch (http://bootswatch.com/) theme.
    #
    # Options are nothing (default) or the name of a valid theme
    # such as "cosmo" or "sandstone".
    #
    # The set of valid themes depend on the version of Bootstrap
    # that's used (the next config option).
    #
    # Currently, the supported themes are:
    # - Bootstrap 2: https://bootswatch.com/2
    # - Bootstrap 3: https://bootswatch.com/3
    'bootswatch_theme': 'united',

    # Choose Bootstrap version.
    # Values: "3" (default) or "2" (in quotes)
    'bootstrap_version': "3",
}

# -- Autodoc options ---------------------------------------------------------
autoclass_content = 'both'

# -- Autoapi options ---------------------------------------------------------


def setup(app):
    app.add_stylesheet("style.css")
