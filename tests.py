import memo
import unittest
import sys
from guppy import hpy  # must install guppy to run tests (I use a separate conda env for this)
import functools
import time
import logging
import random

logger = logging.getLogger('memo')

logging.basicConfig()
logger.setLevel(logging.INFO)

sys.setrecursionlimit(2000) # allows for heavier tests with the fibonacci function


def slowdown(fn): # the caveat is that this doesn't slow down the internal recursive calls of fibonacci
    @functools.wraps(fn)
    def closure(*args, **kwargs):
        ret = fn(*args, **kwargs)
        time.sleep(0.05)
        return ret
    return closure


PROF_DATA = {}


def profile_time(fn):
    @functools.wraps(fn)
    def with_profiling(*args, **kwargs):
        start_time = time.time()

        ret = fn(*args, **kwargs)

        elapsed_time = time.time() - start_time

        if fn.__name__ not in PROF_DATA:
            PROF_DATA[fn.__name__] = {'count': 0, 'times': [], 'max': -1, 'avg': -1}
        PROF_DATA[fn.__name__]['count'] += 1
        PROF_DATA[fn.__name__]['times'].append(elapsed_time)

        return ret

    return with_profiling


def calc_prof_data():
    for fname, data in PROF_DATA.items():
        max_time = max(data['times'])
        avg_time = sum(data['times']) / len(data['times'])
        #print "Function %s called %d times. " % (fname, data['count']),
        #print 'Execution time max: %.3f, average: %.3f' % (max_time, avg_time)
        PROF_DATA[fname]['max'] = max_time
        PROF_DATA[fname]['avg'] = avg_time

def print_prof_data():
    for fname, data in PROF_DATA.items():
        max_time = PROF_DATA[fname]['max']
        avg_time = PROF_DATA[fname]['avg']
        print "Function %s called %d times. " % (fname, data['count']),
        print 'Execution time max: %.3f, average: %.3f' % (max_time, avg_time)

def calc_and_print_prof_data():
    for fname, data in PROF_DATA.items():
        max_time = max(data['times'])
        avg_time = sum(data['times']) / len(data['times'])
        print "Function %s called %d times. " % (fname, data['count']),
        print 'Execution time max: %.3f, average: %.3f' % (max_time, avg_time)
        PROF_DATA[fname]['max'] = max_time
        PROF_DATA[fname]['avg'] = avg_time


def clear_profile_time():
    global PROF_DATA
    PROF_DATA = {}

@memo.Memo
def fibonacci(n):
    time.sleep(0.02)
    if n < 2:
        return n
    return fibonacci(n - 2) + fibonacci(n - 1)


@memo.Memo(memo_alias='fact')
def factorial(n):
    time.sleep(0.02)
    if n < 2:
        return 1
    return n * factorial(n - 1)

@memo.memo_clean  # memo_clean is lighter and allows for deeper recursion (~x2)
def fibonacci_clean(n):
    time.sleep(0.02)
    if n < 2:
        return n
    return fibonacci_clean(n - 2) + fibonacci_clean(n - 1)


hp = hpy()


class TestCase_memo(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        print "tearDown"
        print "pre tear down: "
        print memo.print_memoized()

        for i in memo.memoized.values():
            i.memo_clear_cache()

        print "post tear down:"
        print memo.print_memoized()

        clear_profile_time()

    def test_memo(self):
        print "----------"
        print "test - preserving cache"
        hp.setrelheap()
        fibonacci(100)
        h = hp.heap()
        print h
        self.assertTrue(h.size > 10000)
        print h.size

    def test_memo_clean(self):
        print "----------"
        print "test - deleting cache after the last call"
        hp.setrelheap()
        fibonacci_clean(100)
        h = hp.heap()
        print h
        self.assertTrue(h.size < 10000)
        print h.size

    def test_memo_clear(self):
        print "----------"
        print "test - preserving cache, clear removes cache"
        hp.setrelheap()
        prev_size = hp.heap().size
        fibonacci(100)
        time.sleep(1)
        memo.memoized['fibonacci'].memo_clear_cache()
        h = hp.heap()
        print h
        print "h.size (h.size - prevSize) =", h.size, h.size - prev_size
        self.assertTrue(h.size - prev_size < 500)
        self.assertTrue(h.size < 1000)

    def test_memo_speed(self):
        print "----------"
        print "test - speed across calls - preserving cache"
        hp.setrelheap()
        slow_fib = profile_time(slowdown(fibonacci))
        fib_seq = [slow_fib(i) for i in xrange(1,51)]
        print fib_seq
        calc_and_print_prof_data() # avg time should be well over > 0.1
        # (it clears the cache between calls, going into fib many times over)
        self.assertTrue(PROF_DATA['fibonacci']['avg'] < 0.1)

    def test_memo_clear_speed(self):
        print "----------"
        print "test - speed across calls - clearing cache on each call"
        hp.setrelheap()
        slow_fib_clean = profile_time(slowdown(fibonacci_clean))
        fib_seq = [slow_fib_clean(i) for i in xrange(1,51)]
        print fib_seq
        calc_and_print_prof_data() # avg time should be >= 0.05 and <= 0.1 in any remotely modern computer
        # (close to 0.05 which is what the recursive call takes as a minimum)
        self.assertTrue(PROF_DATA['fibonacci_clean']['avg'] > 0.1)

    def test_memo_selective_clearing(self):
        pass

    def test_memo_explicit_clear_and_populate_again(self):
        print "----------"
        print "test - explicit clear and populate again - preserving cache"
        hp.setrelheap()
        fibonacci(100)
        h = hp.heap()
        print "before clearing"
        print h
        print memo.memoized
        time.sleep(1)
        memo.memoized['fibonacci'].memo_clear_cache()
        h = hp.heap()
        print "after clearing"
        print h
        fibonacci(100)
        h = hp.heap()
        print "repopulated"
        print h
        self.assertTrue(h.size > 10000)
        print h.size

    def test_memo_cannot_memoize_the_same_function_twice(self):
        pass

    def test_memo_multiple_param(self):
        @memo.Memo(clean=True)
        def fibonacci2(n, addn=0, multn=1):
            n += addn
            n *= multn
            if n < 2:
                return n
            return fibonacci2(n - 2) + fibonacci2(n - 1)

        x = fibonacci2(10, multn=3)
        assert x == 832040, "ASSERT against fixed result"
        x = fibonacci2(20, 5, 2)
        assert x == 12586269025, "ASSERT against fixed result"

        for i in xrange(1,11): # this test is arguably slightly superfluous.
            input_x = random.randint(1,20)
            input_y = random.randint(0,10)
            input_z = random.randint(0,10)
            assert fibonacci2(input_x, addn = input_y, multn = input_z) == fibonacci((input_x + input_y ) * input_z)
            print "random test (fib) n", i, " (x addn multn)", input_x, input_y, input_z

    def test_memo_misc(self):

        class memoize_wrong(object):  # to illustrate caveats of memoizing instance methods
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

            @memo.Memo
            def val(self):
                return self.value

            @memoize_wrong
            def val_(self):
                return self.value

            @memo.Memo
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
        # assert val1() != val2(), "FAIL!"

        o1 = Aclass(1)
        o2 = Aclass(2)

        import time
        import sys
        time.sleep(1)
        should_be_three = o2.plus_one()
        o2.value = 10
        print should_be_three, o2.plus_one(), o1.plus_one()  # 3 3 2
        o1.value = 100
        print should_be_three, o2.plus_one(), o1.plus_one()  # 3 3 2 (expected behaviour) we haven't told the cache to clean

        sys.stdout.flush()
        sys.stderr.flush()
        print "-----"

        print Aclass.plus_one
        # memo.memoized[Aclass.plus_one].memo_clear_cache() # deprecated interface style
        memo.memoized['plus_one'].memo_clear_cache()
        # TODO: include test for functions of the same name in different classes

        o7 = Aclass(7)

        memoed_o7_plus2 = memo.Memo(
            o7.plus_two)  # this format is currently not working - interface should probably respect inspection

        res = memoed_o7_plus2()

        print "res ", res
        o7.value = 200
        res = memoed_o7_plus2()
        print "res ", res
        # memoized[Aclass.plus_two].memo_clear_cache()
        res = memoed_o7_plus2()
        print "res ", res
        print memo.memoized

        print should_be_three, o2.plus_one(), o1.plus_one()  # 3 11 101 (expected behaviour)

        # the cache cannot be expected to track changes in the instance,

        print "end"

    def test_memo_alias(self):
        n = factorial(20)
        print 'memo memoized fact', memo.memoized['fact']._cache

def suite():
    my_suite = unittest.TestSuite()
    my_suite.addTest(unittest.makeSuite(TestCase_memo, 'tests for memo'))
    return my_suite


if __name__ == '__main__':
    #unittest.TestSuite(suite())
    unittest.main()