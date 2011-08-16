# -*- coding: utf-8 -*-

import pkg_resources

# see `pkg_resources.replace`
# ...
# replace = {'pre':'c', 'preview':'c','-':'final-','rc':'c','dev':'@'}.get
# ...

VERSION_TAGS = (
        "g",  # final branch
        "f",  # final
        "c",  # pre(view)
        "@",  # dev
    )

version_tags = map(
        lambda x : "*" + pkg_resources.replace(x),
        ("pre", "preview", "-", "rc", "dev", ),
    )


def parse_version (s, ) :
    """
    For more information, visit the `pkg_resources` documentation page,
    http://packages.python.org/distribute/pkg_resources.html#parsing-utilities

    >>> parse_version("1.0")
    ('1.0', '1', 'f')
    >>> parse_version("1.0-1")
    ('1.0-1', '1', 'g')
    >>> parse_version("1.0dev")
    ('1.0dev', '1', '@')
    >>> parse_version("1.0-1dev")
    ('1.0-1dev', '1', '@g')
    """
    _parsed = pkg_resources.parse_version(s, )
    try :
        _vtags = filter(lambda x : x in version_tags, _parsed, )
    except IndexError :
        _vtags = list()

    _base = list()
    for i in _parsed :
        if i.startswith("*") :
            break

        _base.append(str(int(i)))

    _vf = map(lambda x : ("*g" if x == "*final-" else x)[1:], _vtags, )
    _vf.sort()
    return (
            s,  # original
            ".".join(_base),  # base version
            "".join(_vf) if _vtags else "f",  # tags
        )


if __name__ == "__main__"  :
    import doctest
    doctest.testmod()

