# -*- coding: utf-8 -*-

class Forbidden (Exception, ) :
    code = 403
    content = "Forbidden"


class Unauthorized (Exception, ) :
    code = 401
    content = "Unauthorized"


class BadRequest (Exception, ) :
    code = 400
    content = "Bad Request"



if __name__ == "__main__"  :
    import doctest
    doctest.testmod()

