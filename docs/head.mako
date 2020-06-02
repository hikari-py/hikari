<nav id="main-nav" class="navbar navbar-dark navbar-expand-lg bg-dark">
    <a class="navbar-brand" href="${root_url}"><img class="d-inline-block align-top" src="${site_logo}" id="logo" alt="hikari logo" loading="lazy"/>Hikari</a>

    <div class="collapse navbar-collapse" id="navbarNavDropdown">
        <ul class="navbar-nav">
            <li class="nav-item"><a class="nav-link" href="/hikari/index.html">Home</a></li>
            <li class="nav-item active"><a class="nav-link" href="/hikari/hikari/index.html">Documentation</a></li>
            <li class="nav-item"><a class="nav-link" href="https://gitlab.com/nekokatt/hikari">GitLab</a></li>
            <li class="nav-item"><a class="nav-link" href="https://pypi.org/project/hikari">PyPI</a></li>
            <li class="nav-item"><a class="nav-link" href="https://discord.gg/Jx4cNGG">Discord Server</a></li>
        </ul>
    </div>
        
    <form class="form-inline my-2 my-lg-0">
        <div class="gcse-search"
            data-as_oq="${' '.join(search_query.strip().split()) | h }"
            data-gaCategoryParameter="${module.refname | h}">
        </div>
    </form>

    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNavDropdown" aria-controls="navbarNavDropdown" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
    </button>
</nav>