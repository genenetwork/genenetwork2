def numify(number, singular=None, plural=None):
    """Turn a number into a word if less than 13 and optionally add a singular or plural word

    >>> numify(3)
    'three'

    >>> numify(1, 'item', 'items')
    'one item'

    >>> numify(9, 'book', 'books')
    'nine books'

    You can add capitalize to change the capitalization
    >>> numify(9, 'book', 'books').capitalize()
    'Nine books'

    Or capitalize every word using title
    >>> numify(9, 'book', 'books').title()
    'Nine Books'

    >>> numify(15)
    '15'

    >>> numify(0)
    '0'

    >>> numify(12334, 'hippopotamus', 'hippopotami')
    '12,334 hippopotami'

    """
    num_repr = {1 : "one",
                2 : "two",
                3 : "three",
                4 : "four",
                5 : "five",
                6 : "six",
                7 : "seven",
                8 : "eight",
                9 : "nine",
                10 : "ten",
                11 : "eleven",
                12 : "twelve"}

    #Below line commented out cause doesn't work in Python 2.4
    #assert all((singular, plural)) or not any((singular, plural)), "Need to pass two words or none"
    if number == 1:
        word = singular
    else:
        word = plural

    if number in num_repr:
        number = num_repr[number]
    elif number > 9999:
        number = commify(number)

    if word:
        return "%s %s" % (number, word)
    else:
        return str(number)


def commify(n):
    """Add commas to an integer n.

    See http://stackoverflow.com/questions/3909457/whats-the-easiest-way-to-add-commas-to-an-integer-in-python
    But I (Sam) made some small changes based on http://www.grammarbook.com/numbers/numbers.asp

    >>> commify(1)
    '1'
    >>> commify(123)
    '123'
    >>> commify(1234)
    '1234'
    >>> commify(12345)
    '12,345'
    >>> commify(1234567890)
    '1,234,567,890'
    >>> commify(123.0)
    '123.0'
    >>> commify(1234.5)
    '1234.5'
    >>> commify(1234.56789)
    '1234.56789'
    >>> commify(123456.789)
    '123,456.789'
    >>> commify('%.2f' % 1234.5)
    '1234.50'
    >>> commify(None)
    >>>

    """
    if n is None:
        return None

    n = str(n)

    if len(n) <= 4:    # Might as well do this early
        return n

    if '.' in n:
        dollars, cents = n.split('.')
    else:
        dollars, cents = n, None

    # Don't commify numbers less than 10000
    if len(dollars) <= 4:
        return n

    r = []
    for i, c in enumerate(reversed(str(dollars))):
        if i and (not (i % 3)):
            r.insert(0, ',')
        r.insert(0, c)
    out = ''.join(r)
    if cents:
        out += '.' + cents
    return out


if __name__ == '__main__':
    import doctest
    doctest.testmod()
