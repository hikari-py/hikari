## Copyright (c) 2020 Nekokatt

## Permission is hereby granted, free of charge, to any person obtaining a copy
## of this software and associated documentation files (the "Software"), to deal
## in the Software without restriction, including without limitation the rights
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
## copies of the Software, and to permit persons to whom the Software is
## furnished to do so, subject to the following conditions:

## The above copyright notice and this permission notice shall be included in all
## copies or substantial portions of the Software.

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
        <meta property="og:image" content="${site_logo}">
        <meta property="og:description" content="${site_description}">
        <meta property="theme-color" content="${site_accent}">
        <link rel="shortcut icon" type="image/png" href="${site_logo}">

        ## Bootstrap 4 stylesheet
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/${bootstrap_version}/css/bootstrap.min.css">
        ## Custom stylesheets
        <style>
            <%include file="css.mako"/>
        </style>


        ## Provide LaTeX math support
        <script async src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/${mathjax_version}/latest.js?config=TeX-AMS_CHTML'></script>
    </head>

    <body>

        <%include file="head.mako"/>

        <div class="jumbotron jumbotron-fluid">
            <div class="container">
                <h1 class="display-4" id="title-banner">
                    <span id="info"></span> <code><span id="query"></span></code>
                    <small><span id="results-count"></span></small>
                    <noscript>Your browser does not support JavaScript, so search functionality is not available!</noscript>
                </h1>
            </div>
        </div>
        ## We do this here so that browsers that don't support JavaScript show the other message instead of this one
        <script>
            document.getElementById('info').textContent = "Searching...";
        </script>

        <div class="container-xl">
            <div class="container" id="search-results">
            </div>
        </div>

        ## Script dependencies for Bootstrap.
        <script src="https://code.jquery.com/jquery-${jquery_version}.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/popper.js@${popperjs_version}/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/${bootstrap_version}/js/bootstrap.min.js"></script>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/lunr.js/2.3.8/lunr.min.js" integrity="sha512-HiJdkRySzXhiUcX2VweXaiy8yeY212ep/j51zR/z5IPCX4ZUOxaf6naJ/0dQL/2l+ZL+B9in/u4nT8QJZ/3mig==" crossorigin></script>
        <script src="index.js"></script>
        <script src="prebuilt_index.js"></script>
        <script>
            'use strict';
            var lunr_index;
            search(decodeURIComponent(new URL(window.location).hash.substring(1)));

            async function search(query) {
                if (!query) {
                    $("#title-banner").text("No query provided, so there is nothing to search.");
                    return;
                }

                lunr_index = await load_index().catch(err => {
                    $("#title-banner").text("Failed to load search index");
                    throw err;
                });

                await _search(query).catch(err => {
                    var text;
                    if (err.message) {
                        text = "Uncaught error";
                    } else {
                        text = "Malformed query";
                    }
                    $("#title-banner").text(text);
                    throw err;
                });
            }
            async function load_index() {
                try{
                    return lunr.Index.load(PREBUILT_INDEX);
                } catch {
                    // No prebuilt index available, build instead.
                    return lunr(function () {
                        this.ref('i');
                        this.field('ref', { boost: 10 });
                        this.field('name', { boost: 5 });
                        this.field('doc');
                        this.metadataWhitelist = ['position'];
                        index.INDEX.forEach((doc, i) => {
                            const parts = doc.ref.split('.');
                            doc['name'] = parts[parts.length - 1];
                            doc['i'] = i;
                            this.add(doc);
                        }, this);
                    });
                }
            }
            async function _search(query) {
                const initial_query = query;
                const fuzziness = ${int(lunr_search.get('fuzziness', 1))};
                if (fuzziness) {
                    query = query.split(/\s+/)
                            .map(str => str.includes('~') ? str : str + '~' + fuzziness).join(' ');
                }
                const results = lunr_index.search(query);
                $("#info").text("Showing results for");
                $("#query").text(initial_query);

                if (results.length != 1) {
                    $("#results-count").text("(" + results.length + " results)");
                } else {
                    $("#results-count").text("(1 result)");
                }

                results.forEach(function (result) {
                    const dobj = index.INDEX[parseInt(result.ref)];
                    const docstring = dobj.doc;
                    const url = index.URLS[dobj.url] + '#' + dobj.ref;
                    const pretty_name = dobj.ref + (dobj.func ? '()' : '');
                    let text = Object.values(result.matchData.metadata)
                            .filter(({doc}) => doc !== undefined)
                            .map(({doc: {position}}) => {
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
                    document.getElementById('search-results').innerHTML += text;
                });
            }
        </script>


        <!-- Search script and dependencies -->
        <script>
            const input = document.getElementById('lunr-search');
            input.disabled = false;
            input.form.addEventListener('submit', (ev) => {
                ev.preventDefault();
                const url = new URL(window.location);
                url.searchParams.set('q', input.value);
                history.replaceState({}, null, url.toString());
                search(input.value);
            });
            // On page load
            const query = new URL(window.location).searchParams.get('q');
            if (query)
                search(query);
            function search(query) {
                const url = '${'../' * (module.url().count('/') - 1)}search.html#' + encodeURIComponent(query);
                window.location.href = url;
            };
        </script>
    </body>
</html>

