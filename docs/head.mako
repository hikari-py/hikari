<%
    import hikari
%>



<nav id="main-nav" class="navbar navbar-dark navbar-expand-lg bg-dark">
    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNavDropdown" aria-controls="navbarNavDropdown" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"/>
    </button>

    <a class="navbar-brand" href="${root_url}"><img class="d-inline-block align-top" src="${site_logo}" id="logo" alt="hikari logo" loading="lazy"/>Hikari <small>v${hikari.__version__}</small></a>

    <div class="collapse navbar-collapse" id="navbarNavDropdown">
        <ul class="navbar-nav mr-auto">
            <li class="nav-item"><a class="nav-link" href="/hikari/index.html">Home</a></li>
            <li class="nav-item active"><a class="nav-link" href="/hikari/hikari/index.html">Documentation</a></li>
            <li class="nav-item"><a class="nav-link" href="https://github.com/nekokatt/hikari">GitHub</a></li>
            <li class="nav-item"><a class="nav-link" href="https://pypi.org/project/hikari">PyPI</a></li>
            <li class="nav-item"><a class="nav-link" href="https://discord.gg/Jx4cNGG">Discord Server</a></li>
        </ul>

        <form class="form-inline" >
            <input class="form-control mr-sm-2" type="search" placeholder="Search" aria-label="Search" id="lunr-search"/>
            <button class="btn btn-outline-success my-2 my-sm-0" type="submit">&gt;</button>
        </form>
    </div>
</nav>
