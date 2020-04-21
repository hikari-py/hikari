<!--
 | Copyright © Nekoka.tt 2019-2020
 |
 | This file is part of Hikari.
 |
 | Hikari is free software: you can redistribute it and/or modify
 | it under the terms of the GNU Lesser General Public License as published by
 | the Free Software Foundation, either version 3 of the License, or
 | (at your option) any later version.
 |
 | Hikari is distributed in the hope that it will be useful,
 | but WITHOUT ANY WARRANTY; without even the implied warranty of
 | MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 | GNU Lesser General Public License for more details.
 |
 | You should have received a copy of the GNU Lesser General Public License
 | along with Hikari. If not, see <https://www.gnu.org/licenses/>.
 !-->
<%!
    import os
    from pdoc.html_helpers import minify_css
%>
% if "CI_MERGE_REQUEST_IID" in os.environ:
    <script data-project-id="${os.environ['CI_PROJECT_ID']}"
            data-merge-request-id="${os.environ['CI_MERGE_REQUEST_IID']}"
            data-mr-url="https://gitlab.com"
            data-project-path="${os.environ['CI_PROJECT_PATH']}"
            id="review-app-toolbar-script"
            src="https://gitlab.com/assets/webpack/visual_review_toolbar.js">
    </script>
% endif

<link rel="shortcut icon" type="image/png" href="https://assets.gitlab-static.net/uploads/-/system/project/avatar/12050696/Hikari-Logo_1.png"/>
% if "." in module.name:
    <meta property="og:title" content="${module.name.lower()} module documentation" />
% else:
    <meta property="og:title" content="${module.name.capitalize()} API Documentation" />
% endif
<meta property="og:type" content="website" />
<meta property="og:image" content="https://assets.gitlab-static.net/uploads/-/system/project/avatar/12050696/Hikari-Logo_1.png" />
<meta property="og:description" content="A Discord Bot framework for modern Python and asyncio built on good intentions" />
<meta property="theme-color" content="#ff029a" />

<%def name="homelink()" filter="minify_css">
    .homelink {
        display: block;
        font-size: 2em;
        font-weight: bold;
        color: #ffffff;
        border-bottom: .5px;
    }
    .homelink:hover {
        color: inherit;
    }
    .homelink img {
        max-width: 20%;
        max-height: 5em;
        margin: auto;
        margin-bottom: .3em;
        border-radius: 100%;
    }
    .homelink-footer {
        border-bottom: 0em;
        padding: 0em;
        margin-bottom: 0em;
        margain: auto;
    }
</%def>
<%def name="links()" filter="minify_css">
    .links {
        margin: auto;
        margin-top: 0.5em;
        margin-bottom: 1em;
        list-style: none;
        padding: 0em;
        float: left;
        background: transparent;
        color: inherit;
        font-size: 1.2em;
    }
    .links > li {
        display: inline;
    }
</%def>
<style>${homelink()}</style>
<style>${links()}</style>
