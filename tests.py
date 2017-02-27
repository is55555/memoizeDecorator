import memo
import unittest
import sys
from guppy import hpy  # must install guppy to run tests (I use a separate conda env for this)
import functools
import time
import logging

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
        memo.memoized.clear()
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
        memo.memoized.clear()
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


if __name__ == '__main__':
    unittest.main()