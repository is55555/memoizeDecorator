# Memoize decorator
(Tried and tested in Python 2.7)

Implements several decorators for memoization.

Currently a work in progress, although they are functional. Pending tests and a few more sophisticated decorators I have in mind.

# Basic Usage:

    @Memo
    def fibonacci(n):
        if n < 2:
            return n
        return fibonacci(n - 2) + fibonacci(n - 1)

    print [fibonacci(i) for i in xrange(151)]

Sometimes we want to free up the cache when the call is done:

    @Memo(clean = True) # cleans the cache when the call is finished
    def fibonacci(n):
        if n < 2:
            return n
        return fibonacci(n - 2) + fibonacci(n - 1)

    print fibonacci(200)


# Installation

Simply include the corresponding file, it has no dependencies.

# Licence

MIT