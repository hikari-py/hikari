* {
    scrollbar-color: #202324 #454a4d;
    scroll-behavior: smooth;
}

img#logo {
    border-radius: 15px;
    width: 30px;
    height: 30px;
    margin-right: 0.5em;
}

small.smaller {
    font-size: 0.75em;
}

body {
    background-color: #181A1B;
    color: #C9C5C0;
}

h1 {
    margin-top: 3rem;
}

h2 {
    margin-top: 1.75rem;
    margin-bottom: 1em;
}

h3 {
    margin-top: 1.25rem;
}

h4 {
    margin-top: 1rem;
}

.nav-section {
    margin-top: 2em;
}

.monospaced {
    font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

a.sidebar-nav-pill,
a.sidebar-nav-pill:active,
a.sidebar-nav-pill:hover {
    color: #BDB7AF;
}

.module-source > details > pre {
    display: block;
    overflow-x: auto;
    overflow-y: auto;
    max-height: 600px;
    font-size: 0.8em;
}

a {
    color: #DE4F91;
}

a:hover {
    color: #64B1F2;
}

.jumbotron {
    background-color: #232627;
}

.breadcrumb-item.inactive > a {
    color: #d264d0 !important;
}

.breadcrumb-item.active > a {
    color: #de4f91 !important;
}

.breadcrumb-item+.breadcrumb-item::before {
    content: ".";
}

.module-breadcrumb {
    padding-left: 0 !important;
    background-color: #232627;
}

ul.nested {
    margin-left: 1em;
}

h2#parameters::after {
    margin-left: 2em;
}

dt {
    margin-left: 2em;
}

dd {
    margin-left: 4em;
}

dl.no-nest > dt {
    margin-left: 0em;
}

dl.no-nest > dd {
    margin-left: 2em;
}

dl.root {
    margin-bottom: 2em;
}

.definition {
    display: block;
    margin-bottom: 8em !important;
}

.definition .row {
    display: block;
    margin-bottom: 4em !important;
}

.definition h2 {
    font-size: 1em;
    font-weight: bolder;
}

.sep {
    height: 2em;
}

code {
    color: #DB61D9;
}

## Check this to change it 
code .active {
    color: #e83e8c;
}

code a {
    color: #E94A93;
}

a.dotted:hover, abbr:hover {
    text-decoration: underline #9E9689 dotted !important;
}

a.dotted, abbr {
    text-decoration: none !important;
}

## Custom search formatting to look somewhat bootstrap-py
.gsc-search-box, .gsc-search-box-tools, .gsc-control-cse {
    background: none !important;
    border: none !important;
}

.gsc-search-button-v2, .gsc-search-button-v2:hover, .gsc-search-button-v2:focus {
    color: var(--success) !important;
    border-color: var(--success) !important;
    background: none !important;
    padding: 6px 32px !important;
    font-size: inherit !important;
}

.gsc-search-button-v2 > svg {
    fill: var(--success) !important;
}

.gsc-input-box {
    border-radius: 3px;
}

.gsc-control-cse {
    width: 300px !important;
    margin-top: 0 !important;
}

.gsc-control-cse .gsc-control-cse-en {
    margin-top: 0 !important;
}

.bg-dark {
    background-color: #2C2F31 !important;
}

.text-muted {
    color: #9E9689 !important;
}

.alert-primary {
    color: #7CC3FF;
    background-color: #262A2B;
    border-color: #003B7B;
}

.alert-secondary {
    color: #C2BCB4;
    background-color: #282B2C;
    border-color: #3B4042;
}

.alert-success {
    color: #99E6AB;
    background-color: #1A3E29;
    border-color: #255A32;
}

.alert-info {
    color: #8EE3F1;
    background-color: #143B43;
    border-color: #1E5961;
}

.alert-warning {
    color: #FBD770;
    background-color: #513E00;
    border-color: #7B5C00;
}

.alert-danger {
    color: rgb(225, 134, 143);
    background-color: rgb(67, 12, 17);
    border-color: rgb(104, 18, 27);
}

mark {
    background-color: #333333;
    border-radius: 0.1em;
    color: #DB61D9;
}
