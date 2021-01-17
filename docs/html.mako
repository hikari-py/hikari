## Copyright (c) 2020 Nekokatt
## Copyright (c) 2021 davfsa
##
## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
## SOFTWARE.
############################# IMPORTS ##############################
<%!
    import os
    from pdoc import html_helpers
%>
########################### CONFIGURATION ##########################
<%include file="config.mako"/>
############################ COMPONENTS ############################
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

        % if module_list:
            <title>${module.name} module list</title>
            <meta name="description" content="A list of documented Python modules.">
        % else:
            <title>${module.name} API documentation</title>
            <meta name="description" content="${module.docstring | html_helpers.glimpse, trim}">
        % endif

        ## Determine how to name the page.
        % if "." in module.name:
            <meta property="og:title" content="${module.name.lower()} module list">
        % else:
            <meta property="og:title" content="${module.name.capitalize()} API documentation">
        % endif

        <meta property="og:type" content="website">
        <meta property="og:image" content="${site_logo_url}">
        <meta property="og:description" content="${site_description}">
        <meta property="theme-color" content="${site_accent}">
        <link rel="shortcut icon" type="image/png" href="${'../' * module.url().count('/')}${site_logo_name}">

        ## Google Search Engine integration
        <!--<script async src="https://cse.google.com/cse.js?cx=017837193012385208679:pey8ky8gdqw"></script>
        <style>.gsc-control-cse {padding:0 !important;margin-top:1em}</style>-->

        ## Bootstrap 4 stylesheet
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/${bootstrap_version}/css/bootstrap.min.css">
        ## Highlight.js stylesheet
        <link href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${highlightjs_version}/styles/${hljs_style}.min.css" rel="stylesheet">
        ## Custom stylesheets
        <style>
            <%include file="css.mako"/>
        </style>

        ## Provide LaTeX math support
        <script async src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/${mathjax_version}/latest.js?config=TeX-AMS_CHTML'></script>
    </head>

    <body>
        <%include file="body.mako"/>
        ## Script dependencies for Bootstrap.
        <script src="https://code.jquery.com/jquery-${jquery_version}.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/popper.js@${popperjs_version}/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/${bootstrap_version}/js/bootstrap.min.js"></script>
        ## Highlightjs stuff
        <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${highlightjs_version}/highlight.min.js"></script>
        <script>hljs.initHighlightingOnLoad()</script>
    </body>
</html>
