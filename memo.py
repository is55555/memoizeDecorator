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
                logging.warning("memo_clean warning: arguments not hashable, string conversion used instead -> %s", key)
                try:
                    key = cPickle.dumps((args, kwargs))
                except cPickle.PicklingError:
                    logging.error("memo_clean error: could not store result -> %s", key)
                    return f(*args, **kwargs) # executing anyway (could have chosen to just panic)
            if key not in _cache:
                _cache[key] = f(*args, **kwargs)
                logging.info("memo_clean cache MISS -> %s", str(key))
            else:
                logging.info("memo_clean cache HIT  -> %s", str(key))
            return _cache[key]
        finally:
            _call_count[0] -= 1
            if _call_count[0] == 0:
                _cache.clear()
                logging.info("memo_clean cleared cache")

    return closure

# the following is cleaner but allows for less recursion (takes more stack space) - apparently ~2x
class MemoClean(object):
    "clears cache on last return"

    def __init__(self, func):
        self.func = func
        self._call_count = 0
        self._cache = {}

    def __call__(self,  *args, **kwargs):
        self._call_count += 1
        logging.info("memo_clean call count %s", self._call_count)
        try:
            try: # this block finds out whether the arguments are hashable
                if len(kwargs) != 0: raise ValueError
                hash(args) # will raise TypeError if args is unhashable, for instance if it's a list.
                key = (args,) # the args are preserved anyway rather than their hashes
            except (ValueError, TypeError): # if the arguments are not hashable
                logging.warning("memo_clean warning: arguments not hashable, string conversion used instead -> %s", key)
                try:
                    key = cPickle.dumps((args, kwargs))
                except cPickle.UnpicklingError:
                    logging.error("memo_clean error: could not store result -> %s", key)
                    return self.func(*args, **kwargs)  # executing anyway (could have chosen to just panic)
            if key not in self._cache:
                self._cache[key] = self.func(*args, **kwargs)
                logging.info("memo_clean cache MISS -> %s", str(key))
            else:
                logging.info("memo_clean cache HIT  -> %s", str(key))
            return self._cache[key]
        finally:
            self._call_count -= 1
            if self._call_count == 0:
                self._cache.clear()
                logging.info("memo_clean cleared cache")

# this version takes kwargs
class Memo(object):
    def __init__(self, func):
        self.func = func
        self._cache = {}

    def __call__(self, *args, **kwargs):
        key = args
        if kwargs:
            items = kwargs.items()
            items.sort()
            key += tuple(items)
        try:
            if key in self._cache:
                return self._cache[key] # returned stored value (cache hit)
            self._cache[key] = result = self.func(*args, **kwargs) # actually calls func and stores (cache miss)
            return result
        except TypeError:
            try:
                dump = cPickle.dumps(key)
            except cPickle.PicklingError:
                return self.func(*args, **kwargs)
            else:
                if dump in self._cache:
                    return self._cache[dump]
                self._cache[dump] = result = self.func(*args, **kwargs)
                return result


if __name__ == "__main__":
    #logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.WARNING)
    # logging.basicConfig(filename='logfile.log', level=logging.DEBUG)

    @Memo
    @MemoClean
#    @memo_clean # memo_clean is lighter and allows for deeper recursion (~x2)
    def fibonacci(n):
        if n < 2:
            return n
        return fibonacci(n - 2) + fibonacci(n - 1)

    import sys
    print sys.getrecursionlimit()
 #   sys.setrecursionlimit(2000)

    #result = fibonacci(161)
    result = fibonacci(162)

    #result = fibonacci(166)
    #result = fibonacci(167)

    print fibonacci(330)
#    print fibonacci(331) # fails with MemoClean
    #print fibonacci(662)
#    print fibonacci(663) # fails with memo_clean

    #result = fibonacci(300)
    #assert result, 222232244629420445529739893461909967206666939096499764990979600
    print result


    print [fibonacci(i) for i in xrange(151)]


