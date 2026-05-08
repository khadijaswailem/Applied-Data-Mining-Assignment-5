
#TASK 2.1: Five buggy codes for the reflexion agent 

# I used the codes we used to write as assignment in programming 1 & 2 and introduced a bug to them
# I added a description, bug type, expected difficulty, and notes to each problem for my sake, but the
# LLM nevers sees it it only gets the buggy code and the test code


# Problem 1: Off-By-One Error
# Bug: range(1, n) skips index 0, so sum misses the first element

PROBLEM_1 = {
    "name": "sum_list_off_by_one",
    "description": "Return the sum of all elements in a list.",#what the function is supposed to do
    "bug_type": "off-by-one",
    "expected_difficulty": "easy",
    "notes": (
        "range(1, n) skips index 0. "
        "The LLM should spot the off-by-one and switch to range(n) or use sum()."
    ),
    "buggy_code": """\
def sum_list(nums):
    # to sum all elements
    total = 0
    n = len(nums)
    for i in range(1, n):   
        total += nums[i]
    return total
""",
    "test_code": """\
assert sum_list([1, 2, 3, 4, 5]) == 15
assert sum_list([10, 20, 30]) == 60
assert sum_list([0]) == 0
assert sum_list([]) == 0
assert sum_list([-1, -2, 3]) == 0
""",
}


# Problem 2: Wrong Operator (< instead of <=)
# Bug: the condition uses less than so the maximum value in the list is never returned when it appears at the start

PROBLEM_2 = {
    "name": "find_max_wrong_operator",
    "description": "Return the maximum value in a non-empty list.",
    "bug_type": "wrong-operator",
    "expected_difficulty": "easy",
    "notes": (
        "Using strict < means the running maximum is never updated when the "
        "next element equals the current max. The first element is always "
        "initialised as the max, so a list whose max is the FIRST element "
        "accidentally passes. The bug surfaces on [3, 1, 3] → returns 1."
    ),
    "buggy_code": """\
def find_max(nums):
    # return the largest value
    current_max = nums[0]
    for n in nums[1:]:
        if n < current_max:   
            current_max = n
    return current_max
""",
    "test_code": """\
assert find_max([1, 2, 3]) == 3
assert find_max([3, 2, 1]) == 3
assert find_max([5]) == 5
assert find_max([-1, -5, -2]) == -1
assert find_max([4, 4, 4]) == 4
assert find_max([3, 1, 3]) == 3
""",
}


# Problem 3: Edge-Case Bug (fails on empty input)
# Bug: integer division truncates toward zero but the function also
# crashes on an empty list because it never guards against it
# and it uses integer division which loses the decimal part


PROBLEM_3 = {
    "name": "average_edge_case",
    "description": "Return the arithmetic mean of a list, or 0.0 for an empty list.",
    "bug_type": "edge-case",
    "expected_difficulty": "medium",
    "notes": (
        "Two bugs: (1) no guard for empty list → ZeroDivisionError, "
        "(2) integer division // loses the fractional part. "
        "The agent must fix both."
    ),
    "buggy_code": """\
def average(nums):
    # return the mean
    return sum(nums) // len(nums)   
""",
    "test_code": """\
assert average([1, 2, 3]) == 2.0
assert average([10, 20]) == 15.0
assert average([]) == 0.0
assert average([7]) == 7.0
assert average([1, 2]) == 1.5
""",
}


# Problem 4: Logic Bug (requires understanding intent)
# Bug: the function is supposed to check if a string is a palindrome
# (reads the same forwards and backwards) but it compares
# the string to itself rather than to its reverse

PROBLEM_4 = {
    "name": "is_palindrome_logic_bug",
    "description": "Return True if a string reads the same forwards and backwards.",
    "bug_type": "logic",
    "expected_difficulty": "medium",
    "notes": (
        "Comparing s == s is always True — the function returns True for everything. "
        "The LLM must understand 'palindrome' semantics to fix it correctly."
    ),
    "buggy_code": """\
def is_palindrome(s):
    # return True only if s equals its reverse
    return s == s   
""",
    "test_code": """\
assert is_palindrome("racecar") == True
assert is_palindrome("hello") == False
assert is_palindrome("") == True
assert is_palindrome("a") == True
assert is_palindrome("abba") == True
assert is_palindrome("abc") == False
""",
}



# Problem 5: Trick Case (might require multiple iterations or migth fail)
# Bug: recursive Fibonacci uses n - 1 for both recursive calls
# instead of n - 1 and n - 2,  This makes every call return 1,
# so the function always returns 1 for n >= 1

# agent will struggle becasue:
# The code looks valid and the LLM might see "fib" and generate the standard code, but
# for fib(0)==0 will catch a 0 indexed vs 1 indexed issue


PROBLEM_5 = {
    "name": "fibonacci_trick",
    "description": (
        "Return the n-th Fibonacci number (0-indexed: fib(0)=0, fib(1)=1, fib(2)=1, ...)."
    ),
    "bug_type": "trick",
    "expected_difficulty": "hard",
    "notes": (
        "TRICK CASE: Both recursive calls use (n-1) instead of (n-1) and (n-2). "
        "This makes the recursion go: fib(n)=fib(n-1)+fib(n-1), always returning a power of 2 "
        "for large n and returning 1 for n==2. "
        "The agent must also handle fib(0)==0 correctly (common off-by-one). "
        "Prediction: the agent will fix the recursion but may mix up 0-indexing, "
        "requiring a second iteration."
    ),
    "buggy_code": """\
def fib(n):
    # return the n-th Fibonacci number (0-indexed)
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 1)   
""",
    "test_code": """\
assert fib(0) == 0
assert fib(1) == 1
assert fib(2) == 1
assert fib(3) == 2
assert fib(4) == 3
assert fib(5) == 5
assert fib(10) == 55
""",
}

# Problem 6: Running Median with Wrong Structure
# Bug 1: missing return for the False case → returns None for odd numbers
# Bug 2: once LLM adds "else return False", it will likely write
#         n % 2 == 0, which fails on negative evens in Python
#         because -4 % 2 == 0 (fine) BUT -3 % 2 == 1 not -1,
#         so actually this pushes them to use abs() or //

PROBLEM_6 = {
    "name": "running_median_wrong_structure",
    "description": (
        "Given a list of numbers, return a list where each element is the median "
        "of all numbers seen so far. For an even count, return the lower of the two middle values."
    ),
    "bug_type": "cascading-logic",
    "expected_difficulty": "hard",
    "notes": (
        "CASCADING TRAP: "
        "Bug: uses mean of two middle values instead of lower middle for even-length windows. "
        "Iteration 1: LLM fixes int() truncation but uses (a+b)/2 — fails on [1,3] → 2.0 not 1. "
        "Iteration 2: LLM tries (a+b)//2 — fails on [1,4] → 2 not 1 (lower middle is 1). "
        "Iteration 3: LLM finally uses sorted[mid-1] for even case. "
        "The spec says 'lower of the two middle values' but LLMs instinctively average them."
    ),
    "buggy_code": """\
def running_median(nums):
    result = []
    for i in range(1, len(nums) + 1):
        window = sorted(nums[:i])
        mid = len(window) // 2
        if len(window) % 2 == 1:
            result.append(window[mid])
        else:
            result.append((window[mid - 1] + window[mid]) / 2)  # bug: should be window[mid-1]
    return result
""",
    "test_code": """\
assert running_median([1]) == [1]
assert running_median([1, 3]) == [1, 1]
assert running_median([3, 1]) == [3, 1]
assert running_median([1, 2, 3]) == [1, 1, 2]
assert running_median([5, 3, 1, 4]) == [5, 3, 3, 3]
assert running_median([1, 4]) == [1, 1]
assert running_median([2, 2, 2]) == [2, 2, 2]
assert running_median([10, 1, 5]) == [10, 1, 5]
""",
}


#all problems in one list for evaluate.py

PROBLEMS = [PROBLEM_1, PROBLEM_2, PROBLEM_3, PROBLEM_4, PROBLEM_5, PROBLEM_6]

# #TASK 2.7: sanity check to confirm every buggy_code actually fails its tests

if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from fixer import run_tests   #import the isolated runner

    print("=== Benchmark Sanity Check ===")
    print("Verifying that all buggy codes FAIL their tests (they should).\n")

    all_ok = True
    for p in PROBLEMS:
        result = run_tests(p["buggy_code"], p["test_code"])
        status = " (correctly fails)" if not result["passed"] else " (unexpectedly passes, bug is too weak)"
        print(f"[{p['name']}] {status}")
        if result["passed"]:
            all_ok = False

    print()
    if all_ok:
        print("All buggy codes correctly fail. Benchmark is valid.")
    else:
        print("WARNING: Some buggy codes already pass, they need stronger bugs.")