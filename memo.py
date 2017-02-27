import cPickle
import logging
import functools

logger = logging.getLogger('memo') # could also use  __name__ but I like making it explicit


# light version of memo with clean-up
def memo_clean(f):
    "clears cache on last return"

    _call_count = [0]   # this little hack works around nested function scope ...
                        # ...  (the innermost definition shadows the outer ones) so a simple primitive value...
                        # ... wouldn't work whereas a one-element list does.
    _cache = {}

    @functools.wraps(f) # preserve function names
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
                    logger.error("memo_clean error: could not store result")
                    return f(*args, **kwargs) # executing anyway (could have chosen to just panic)
                logger.info("memo_clean arguments not hashable, string conversion used instead")
            if key not in _cache:
                _cache[key] = f(*args, **kwargs)
                logger.debug("memo_clean cache MISS -> %s", str(key))
            else:
                logger.debug("memo_clean cache HIT  -> %s", str(key))
            return _cache[key]
        finally:
            _call_count[0] -= 1
            if _call_count[0] == 0:
                _cache.clear()
                logger.info("memo_clean cleared cache")

    return closure


memoized = {}

# the following is cleaner but allows for less recursion (takes more stack space) - apparently ~2x
# using clean = True it also cleans the cache at the end of the call (see examples)
class _Memo(object):
    "clears cache on last return"

    def __init__(self, func, clean):
        self.func = func
        functools.update_wrapper(self, func)
        self._call_count = 0
        self._cache = {}
        self._clean = clean
        logger.info("memo_clean mode = %s", clean)
        memoized[self.func] = self

    def __call__(self,  *args, **kwargs):
        self._call_count += 1
        logger.debug("memo_clean call count %s", self._call_count)
        try:
            try: # this block finds out whether the arguments are hashable
                if len(kwargs) != 0: raise ValueError
                hash(args) # will raise TypeError if args is unhashable, for instance if it's a list.
                key = (args,) # the args are preserved anyway rather than their hashes
            except (ValueError, TypeError): # if the arguments are not hashable
                try:
                    key = cPickle.dumps((args, kwargs))
                except cPickle.UnpicklingError:
                    logger.error("memo_clean error: could not store result")
                    return self.func(*args, **kwargs)  # executing anyway (could have chosen to just panic)
                logger.info("memo_clean arguments not hashable, string conversion used instead")
            if key not in self._cache:
                self._cache[key] = self.func(*args, **kwargs)
                logger.debug("memo_clean cache MISS -> %s", str(key))
            else:
                logger.debug("memo_clean cache HIT  -> %s", str(key))
            return self._cache[key]
        finally:
            self._call_count -= 1
            if self._clean and self._call_count == 0:
                self._cache.clear()
                logger.info("memo_clean cleared cache")

    def __str__(self):
        return "Memoized_" + self.func.__name__

    def __get__(self, obj, obj_type=None):  # support instance methods
        if obj is None:
            return self.func
        return functools.partial(self, obj)

    #@classmethod
    def memo_clear_cache(self):
        self._cache.clear()
        logger.info("memo_clean cleared cache explicitly - " + self.func.__name__ + " in " +  str(self))


def Memo(function=None, clean=False): # named uppercase because it simply wraps a class
    if function:
        return _Memo(function, clean=clean)
    else:
#        @functools.wraps(function)
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

    print fibonacci

    class memoize_wrong(object): # to illustrate caveats of memoizing instance methods
        def __init__(self, function):
            self._function = function
            self._cacheName = '_cache__' + function.__name__

        def __get__(self, instance, cls=None):
            self._instance = instance
            return self

        def __call__(self, *args):
            cache = self._instance.__dict__.setdefault(self._cacheName, {})
            if cache.has_key(args):
                return cache[args]
            else:
                object = cache[args] = self._function(self._instance, *args)
                return object

    class Aclass(object):
        def __init__(self, value):
            self.value = value

        @Memo
        def val(self):
            return self.value

        @memoize_wrong
        def val_(self):
            return self.value

        @Memo
        def plus_one(self):
            return self.value + 1

        def plus_two(self):
            return self.value + 2

    val1 = Aclass(1).val
    val2 = Aclass(2).val
    print "->", val1(), val2()
    assert val1() != val2(), "FAIL!"

    val1 = Aclass(1).val_
    val2 = Aclass(2).val_
    print "->", val1(), val2()
    #assert val1() != val2(), "FAIL!"

    o1 = Aclass(1)
    o2 = Aclass(2)

    import time
    import sys
    time.sleep(1)
    should_be_three = o2.plus_one()
    o2.value = 10
    print should_be_three, o2.plus_one(), o1.plus_one() # 3 3 2
    o1.value = 100
    print should_be_three, o2.plus_one(), o1.plus_one() # 3 3 2 (expected behaviour) we haven't told the cache to clean

    sys.stdout.flush()
    sys.stderr.flush()
    print "-----"
    time.sleep(1)
    memoized[Aclass.plus_one].memo_clear_cache()
        # TODO: include test for functions of the same name in different classes

    o7 = Aclass(7)

    memoed_o7_plus2 = Memo(o7.plus_two) # this format is currently not working - interface should probably respect inspection

    res = memoed_o7_plus2()

    print "res ", res
    o7.value = 200
    res = memoed_o7_plus2()
    print "res ", res
    #memoized[Aclass.plus_two].memo_clear_cache()
    res = memoed_o7_plus2()
    print "res ", res
    print memoized


    print should_be_three, o2.plus_one(), o1.plus_one() # 3 11 101 (expected behaviour)

    # the cache cannot be expected to track changes in the instance,

    print "end"

