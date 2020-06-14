## Copyright © Nekoka.tt 2019-2020
##
## This file is part of Hikari.
##
## Hikari is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Hikari is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with Hikari. If not, see <https://www.gnu.org/licenses/>.

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
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

        % if module_list:
            <title>Python module list</title>
            <meta name="description" content="A list of documented Python modules." />
        % else:
            <title>${module.name} API documentation</title>
            <meta name="description" content="${module.docstring | html_helpers.glimpse, trim}" />
        % endif

        ## Determine how to name the page.
        % if "." in module.name:
            <meta property="og:title" content="${module.name.lower()} module documentation" />
        % else:
            <meta property="og:title" content="${module.name.capitalize()} API Documentation" />
        % endif

        <meta property="og:type" content="website" />
        <meta property="og:image" content="${site_logo}" />
        <meta property="og:description" content="${site_description}" />
        <meta property="theme-color" content="${site_accent}" />
        <link rel="shortcut icon" type="image/png" href="${site_logo}"/>

        ## Google Search Engine integration
        <script async src="https://cse.google.com/cse.js?cx=017837193012385208679:pey8ky8gdqw"></script>
        <style>.gsc-control-cse {padding:0 !important;margin-top:1em}</style>

        ## Bootstrap 4 stylesheet
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/${bootstrap_version}/css/bootstrap.min.css"/>
        ## Highlight.js stylesheet
        <link href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${highlightjs_version}/styles/${hljs_style}.min.css" rel="stylesheet"/>
        ## Custom stylesheets
        <style>
            <%include file="css.mako"/>
        </style>


        ## Provide LaTeX math support
        <script async src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/${mathjax_version}/latest.js?config=TeX-AMS_CHTML'></script>

        ## If this is a merge request on GitLab, inject the visual feedback scripts.
        % if "CI_MERGE_REQUEST_IID" in os.environ:
            <% print("Injecting Visual Feedback GitLab scripts") %>
            <script data-project-id="${os.environ['CI_PROJECT_ID']}"
                    data-merge-request-id="${os.environ['CI_MERGE_REQUEST_IID']}"
                    data-mr-url="https://gitlab.com"
                    data-project-path="${os.environ['CI_PROJECT_PATH']}"
                    id="review-app-toolbar-script"
                    data-require-auth="false"
                    src="https://gitlab.com/assets/webpack/visual_review_toolbar.js">
            </script>
        % endif
    </head>

    <body>

        <%include file="body.mako" />

        ## Script dependencies for Bootstrap.
        <script src="https://code.jquery.com/jquery-${jquery_version}.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/popper.js@${popperjs_version}/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/${bootstrap_version}/js/bootstrap.min.js"></script>
        ## Highlightjs stuff
        <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${highlightjs_version}/highlight.min.js"></script>
        <script>hljs.initHighlightingOnLoad()</script>
    </body>
</html>
