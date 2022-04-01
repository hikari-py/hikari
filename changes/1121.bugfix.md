Don't error on an out-of-spec HTTP status code (e.g one of Cloudflare's custom status codes).
`HTTPResponseError.status` may now be of type `http.HTTPStatus` or `int`.
