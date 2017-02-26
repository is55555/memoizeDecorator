# Memoize decorator
(Tried and tested in Python 2.7)

Version: beta (still completing features. Will be alpha when test cases are complete and 0.1, etc. afterwards)

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


Supports caching for methods. User is expected to clear the cache on each Class.method as required if the state of
the instances change in a way that invalidates the cache. More sophisticated behaviour than this is unreasonable to do
at the memoizer level and would induce more mistakes than otherwise. The only reasonable improvement would be caching
by instance instead and clearing instance by instance.

# Installation

Simply include the corresponding file, it has no dependencies.

# Licence

MIT