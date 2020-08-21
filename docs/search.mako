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
            <meta name="description" content="Click here to view results" />
        % endif

        ## Determine how to name the page.
        <meta property="og:title" content="Search results in Hikari" />

        <meta property="og:type" content="website" />
        <meta property="og:image" content="${site_logo}" />
        <meta property="og:description" content="${site_description}" />
        <meta property="theme-color" content="${site_accent}" />
        <link rel="shortcut icon" type="image/png" href="${site_logo}"/>

        ## Bootstrap 4 stylesheet
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/${bootstrap_version}/css/bootstrap.min.css"/>
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
                    Search results for <code><span id="query">???</span></code>
                    <small>(<span id="results-count">0 results</span>)</small>
                </h1>
            </div>
        </div>

        <div class="container-xl">
            <div class="container" id="search-results">
            </div>
        </div>

        ## Script dependencies for Bootstrap.
        <script src="https://code.jquery.com/jquery-${jquery_version}.slim.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/popper.js@${popperjs_version}/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/${bootstrap_version}/js/bootstrap.min.js"></script>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/lunr.js/2.3.8/lunr.min.js" integrity="sha512-HiJdkRySzXhiUcX2VweXaiy8yeY212ep/j51zR/z5IPCX4ZUOxaf6naJ/0dQL/2l+ZL+B9in/u4nT8QJZ/3mig==" crossorigin></script>
        <script src="index.js"></script>
        <script>
            'use strict';
            const lunr_index = build_index();
            search(decodeURIComponent(new URL(window.location).hash.substring(1)));

            async function build_index() {
                return lunr(function () {
                    this.ref('i');
                    this.field('ref', {boost: 10});
                    this.field('name', {boost: 5});
                    this.field('doc');
                    this.metadataWhitelist = ['position'];
                    INDEX.forEach((doc, i) => {
                        const parts = doc.ref.split('.');
                        doc['name'] = parts[parts.length - 1];
                        doc['i'] = i;
                        this.add(doc);
                    }, this);
                });
            }
            function search(query) {
                _search(query).catch(err => {
                    $("#title-banner").text(err.message || "Malformed query");
                    throw err
                });
            }
            async function _search(query) {
                const initial_query = query;
                if (!query) {
                    $("#title-banner").text('No query provided, so there is nothing to search.');
                    return;
                }
                const fuzziness = ${int(lunr_search.get('fuzziness', 1))};
                if (fuzziness) {
                    query = query.split(/\s+/)
                            .map(str => str.includes('~') ? str : str + '~' + fuzziness).join(' ');
                }
                const results = (await lunr_index).search(query);
                $("#query").text(initial_query);

                console.log(results.length);

                if (results.length != 1) {
                    $("#results-count").text(results.length + " results");
                } else {
                    $("#results-count").text("1 result");
                }

                results.forEach(function (result) {
                    const dobj = INDEX[parseInt(result.ref)];
                    const docstring = dobj.doc;
                    const url = URLS[dobj.url] + '#' + dobj.ref;
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
            ## On page load
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

