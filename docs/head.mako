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
<%
    import hikari

    DEPTH = '../' * module.url().count('/')
%>
<nav id="main-nav" class="navbar navbar-dark navbar-expand-lg bg-dark">
    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNavDropdown" aria-controls="navbarNavDropdown" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"/>
    </button>

    <a class="navbar-brand" href="${root_url}"><img class="d-inline-block align-top" src="${DEPTH}${site_logo_name}" id="logo" alt="hikari logo" loading="lazy"/>Hikari <small class="smaller">${hikari.__version__}</small></a>

    <div class="collapse navbar-collapse" id="navbarNavDropdown">
        <ul class="navbar-nav mr-auto">
            <li class="nav-item"><a class="nav-link" href="${DEPTH}index.html">Home</a></li>
            <li class="nav-item"><a class="nav-link active" href="${DEPTH}hikari/index.html">Documentation</a></li>
            <li class="nav-item"><a class="nav-link" href="https://github.com/hikari-py/hikari">GitHub</a></li>
            <li class="nav-item"><a class="nav-link" href="https://pypi.org/project/hikari">PyPI</a></li>
            <li class="nav-item"><a class="nav-link" href="https://discord.gg/Jx4cNGG">Discord Server</a></li>
        </ul>

        <form class="form-inline" action="${DEPTH}hikari/search.html">
            <input class="form-control mr-sm-2" type="search" placeholder="Search" aria-label="Search" id="lunr-search" name="q"/>
            <button class="btn btn-outline-success my-2 my-sm-0" type="submit">&gt;</button>
        </form>
    </div>
</nav>
