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
########################### CONFIGURATION ##########################
<%include file="config.mako"/>
############################ COMPONENTS ############################
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

        <title>Search documentation - ${module.name.capitalize()}</title>
        <meta name="description" content="Click here to view results">

        <meta property="og:title" content="Search documentation - ${module.name.capitalize()}">

        <meta property="og:type" content="website">
        <meta property="og:image" content="${site_logo_url}">
        <meta property="og:description" content="${site_description}">
        <meta property="theme-color" content="${site_accent}">
        <link rel="shortcut icon" type="image/png" href="${'../' * module.url().count('/')}${site_logo_name}">

        ## Bootstrap 4 stylesheet
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/${bootstrap_version}/css/bootstrap.min.css">
        ## Custom stylesheets
        <style>
            <%include file="css.mako"/>
        </style>
    </head>

    <body>
        <%include file="head.mako"/>
        <script src="https://code.jquery.com/jquery-${jquery_version}.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/lunr.js/2.3.8/lunr.min.js" integrity="sha512-HiJdkRySzXhiUcX2VweXaiy8yeY212ep/j51zR/z5IPCX4ZUOxaf6naJ/0dQL/2l+ZL+B9in/u4nT8QJZ/3mig==" crossorigin></script>

        <div class="jumbotron jumbotron-fluid">
            <div class="container">
                <h1 class="display-4" id="title-banner">
                    <span id="info"></span> <code><span id="query"></span></code>
                    <small><span id="results-count"></span></small>
                    <noscript>JavaScript is disabled, so search functionality is not available!</noscript>
                </h1>
            </div>
        </div>

        <div class="container" id="search-results">
        </div>

        <script>
        var Search = {
            init() {
                this._index = null;
                this._data = null;
                this._animate = true;
                this._pending_query = new URL(window.location).searchParams.get('q');

                if (!this._pending_query) {
                    $("#info").text("No query provided, so there is nothing to search.");
                    return;
                }
                this._searching_animation();
                this._load_resources();
            },

            _set_result(message, err) {
                Search._animate = false;
                $("#info").text(message);

                if (err)
                    throw err;
            },

            _load_resources() {
                $.ajax({
                    type: "GET",
                    url: "./index.json",
                    dataType: "json",
                    cache: true,
                    timeout: 2000,
                    complete: this._complete,
                    success: function (data) {
                        Search._data = data;
                        Search._check_pending_query();
                    },
                });
                $.ajax({
                    type: "GET",
                    url: "./prebuilt_index.json",
                    dataType: "json",
                    cache: true,
                    timeout: 2000,
                    complete: this._complete,
                    success: function (data) {
                        Search._index = lunr.Index.load(data);
                        Search._check_pending_query();
                    },
                });
            },

            _complete(_, textstatus) {
                if (textstatus != "success") {
                    Search._set_result("Failed to load resource", "Failed to load resource");
                }
            },

            _check_pending_query() {
                if (this._data !== null && this._index !== null && (q = this._pending_query) !== null) {
                    this._pending_query = null;
                    this._search(q);
                }
            },

            _searching_animation() {
                var i = 3;
                function animate() {
                    if (!Search._animate) {
                        return;
                    }
                    $("#info").text("Searching" + ".".repeat(i));
                    i = (i + 1) % 4;

                    window.setTimeout(animate, 500);
                }
                animate();
            },

            _search(query) {
                try {
                    this._query(query)
                } catch (err) {
                    if (!err.message) {
                        this._set_result("Malformed query", err);
                    }
                    this._set_result("Uncaught error", err);
                }

            },

            _query(query) {
                const initial_query = query;
                const fuzziness = 0;
                if (fuzziness) {
                    query = query.split(/\s+/)
                        .map(str => str.includes('~') ? str : str + '~' + fuzziness).join(' ');
                }

                const results = this._index.search(query);

                var search_results_html = "";
                results.forEach(function (result) {
                    const dobj = Search._data.index[parseInt(result.ref)];
                    const docstring = dobj.d;
                    const url = Search._data.urls[dobj.u] + '#' + dobj.r;
                    const pretty_name = dobj.r + (dobj.f ? '()' : '');
                    var text = Object.values(result.matchData.metadata)
                        .filter(({ d }) => d !== undefined)
                        .map(({ d: { position } }) => {
                            return position.map(([start, length]) => {
                                const PAD_CHARS = 30;
                                const end = start + length;
                                return [
                                    start,
                                    (start - PAD_CHARS > 0 ? '…' : '') +
                                    docstring.substring(start - PAD_CHARS, start) +
                                    '<mark>' + docstring.slice(start, end) + '</mark>' +
                                    docstring.substring(end, end + PAD_CHARS) +
                                    (end + PAD_CHARS < docstring.length ? '…' : '')
                                ];
                            });
                        })
                        .flat()
                        .sort(([pos1,], [pos2,]) => pos1 - pos2)
                        .map(([, text]) => text)
                        .join('')
                        .replace(/……/g, '…');

                    text = '<h4><a href="' + url + '"><code>' + pretty_name + '</code></a></h4><p>' + text + '</p>';
                    search_results_html += text
                });

                this._set_result("Showing results for");
                $("#query").text(initial_query);
                document.getElementById('search-results').innerHTML = search_results_html;

                if (results.length != 1) {
                    $("#results-count").text("(" + results.length + " results)");
                } else {
                    $("#results-count").text("(1 result)");
                }
            },
        }

        $(document).ready(function () {
            Search.init();
        });
        </script>
    </body>
</html>

