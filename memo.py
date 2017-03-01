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

    def __init__(self, func, clean, memo_alias):
        self.func = func
        functools.update_wrapper(self, func)
        self._call_count = 0
        self._cache = {}
        self._clean = clean
        logger.info("memo_clean mode = %s", clean)

        if memo_alias:
            self.slot_name = memo_alias
        else:
            self.slot_name = func.__name__

        logger.info("slot name = %s", self.slot_name)

        if self.slot_name in memoized:
            raise BaseException("already memoized: " + self.slot_name)
        memoized[self.slot_name] = self

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
                logger.info("memo_clean cleared cache - " + self.slot_name)

    def __str__(self):
        return "Memoized_" + self.func.__name__

    def __get__(self, obj, obj_type=None):  # support instance methods
        if obj is None:
            return self.func
        f = functools.partial(self, obj)
        f.__name__ = self.func.__name__
        return f

    def memo_clear_cache(self):
        self._cache.clear()
        logger.info("memo_clean cleared cache explicitly - " + self.func.__name__ + " in " +  str(self))


def Memo(function=None, clean=False, memo_alias = False): # named uppercase because it simply wraps a class
    if function:
        return _Memo(function, clean=clean, memo_alias = memo_alias)
    else:
        def closure(f):
            return _Memo(f, clean=clean, memo_alias = memo_alias)

        return closure


def print_memoized():
    print "{"
    for k, v in memoized.items():
        print k, ":", v._cache, ","
    print "}"

    # import tests # re-importing causes redefinition of the memoized function and a clash

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    #logging.basicConfig(level=logging.WARNING)
    import tests

    suite = tests.unittest.TestLoader().loadTestsFromTestCase(tests.TestCase_memo)
    tests.unittest.TextTestRunner(verbosity=2).run(suite)

    tests.unittest.TestSuite(tests.suite())
