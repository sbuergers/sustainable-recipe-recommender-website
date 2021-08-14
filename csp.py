""" Content security policy (CSP) """

SELF = "'self'"
csp = {
    "default-src": [SELF],
    "style-src": [
        SELF,
        "https://use.fontawesome.com",
        "https://stackpath.bootstrapcdn.com",
        "https://cdn.jsdelivr.net",
    ],
    "style-src-elem": [
        SELF,
        "https://use.fontawesome.com",
        "https://stackpath.bootstrapcdn.com",
        "https://cdn.jsdelivr.net",
    ],
    "script-src": [
        SELF,
        "https://code.jquery.com",
        "https://cdnjs.cloudflare.com",
        "https://stackpath.bootstrapcdn.com",
        "https://cdn.jsdelivr.net",
    ],
    "font-src": [
        SELF,
        "https://use.fontawesome.com",
        "https://stackpath.bootstrapcdn.com",
    ],
    "connect-src": [SELF, "https://cdn.jsdelivr.net"],
    "frame-src": [SELF],
    "frame-ancestors": [SELF],
    "img-src": "*",
}


# eof
