import cPickle
import logging


def memo_clean(f):
    "clears cache on last return"

    _call_count = [0]   # this little hack works around nested function scope ...
                        # ...  (the innermost definition shadows the outer ones) so a simple primitive value...
                        # ... wouldn't work whereas a one-element list does.
    _cache = {}

    def closure(*args, **kwargs):
        _call_count[0] += 1
        try:
            try: # this block finds out whether the arguments are hashable
                if len(kwargs) != 0: raise ValueError
                hash(args) # will raise TypeError if args is unhashable, for instance if it's a list.
                key = (args,) # the args are preserved anyway rather than their hashes
            except (ValueError, TypeError): # if the arguments are not hashable
                try:
                    key = cPickle.dumps((args, kwargs))
                except cPickle.PicklingError:
                    logging.error("memo_clean error: could not store result")
                    return f(*args, **kwargs) # executing anyway (could have chosen to just panic)
                logging.info("memo_clean arguments not hashable, string conversion used instead")
            if key not in _cache:
                _cache[key] = f(*args, **kwargs)
                logging.debug("memo_clean cache MISS -> %s", str(key))
            else:
                logging.debug("memo_clean cache HIT  -> %s", str(key))
            return _cache[key]
        finally:
            _call_count[0] -= 1
            if _call_count[0] == 0:
                _cache.clear()
                logging.info("memo_clean cleared cache")

    return closure

# the following is cleaner but allows for less recursion (takes more stack space) - apparently ~2x
# using clean = True it also cleans the cache at the end of the call (see examples)
class _Memo(object):
    "clears cache on last return"

    def __init__(self, func, clean):
        self.func = func
        self._call_count = 0
        self._cache = {}
        self._clean = clean
        logging.info("memo_clean mode = %s", clean)

    def __call__(self,  *args, **kwargs):
        self._call_count += 1
        logging.debug("memo_clean call count %s", self._call_count)
        try:
            try: # this block finds out whether the arguments are hashable
                if len(kwargs) != 0: raise ValueError
                hash(args) # will raise TypeError if args is unhashable, for instance if it's a list.
                key = (args,) # the args are preserved anyway rather than their hashes
            except (ValueError, TypeError): # if the arguments are not hashable
                try:
                    key = cPickle.dumps((args, kwargs))
                except cPickle.UnpicklingError:
                    logging.error("memo_clean error: could not store result")
                    return self.func(*args, **kwargs)  # executing anyway (could have chosen to just panic)
                logging.info("memo_clean arguments not hashable, string conversion used instead")
            if key not in self._cache:
                self._cache[key] = self.func(*args, **kwargs)
                logging.debug("memo_clean cache MISS -> %s", str(key))
            else:
                logging.debug("memo_clean cache HIT  -> %s", str(key))
            return self._cache[key]
        finally:
            self._call_count -= 1
            if self._clean and self._call_count == 0:
                self._cache.clear()
                logging.info("memo_clean cleared cache")


def Memo(function=None, clean=False):
    if function:
        return _Memo(function, clean=clean)
    else:
        def closure(f):
            return _Memo(f, clean=clean)

        return closure


if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    #logging.basicConfig(level=logging.WARNING)

    @Memo
#    @memo_clean # memo_clean is lighter and allows for deeper recursion (~x2)
    def fibonacci(n):
        if n < 2:
            return n
        return fibonacci(n - 2) + fibonacci(n - 1)

    @Memo(clean = True)
    def fibonacci2(n, addn = 0, multn = 1):
        n += addn
        n *= multn
        if n < 2:
            return n
        return fibonacci2(n - 2) + fibonacci2(n - 1)
    import sys
    print sys.getrecursionlimit()
    sys.setrecursionlimit(2000)

    #result = fibonacci(161)
    result = fibonacci(162)

    #result = fibonacci(166)
    #result = fibonacci(167)

    print fibonacci(330)
#    print fibonacci(331) # first to fail with MemoClean with default recursionlimit
    #print fibonacci(662)
#    print fibonacci(663) # first to fail with memo_clean with default recursionlimit

    #result = fibonacci(300)
    #assert result, 222232244629420445529739893461909967206666939096499764990979600
    print result

    print fibonacci2(10, multn=3)
    print fibonacci2(20, 5, 2)

    print [fibonacci(i) for i in xrange(151)]


