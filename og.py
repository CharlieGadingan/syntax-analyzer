# test_comprehensive.py
# This file has 15 syntax errors - each is clearly marked

# ERROR 1: Missing colon
def function_with_error()  # <-- Missing colon

# ERROR 2: Wrong indentation
  print("This line has wrong indentation")  # <-- Extra space at start

# ERROR 3: Unclosed string
name = 'John  # <-- Missing closing quote

# ERROR 4: Unclosed parenthesis
print("Hello, world"  # <-- Missing closing parenthesis

# ERROR 5: Missing comma in list
numbers = [1 2 3 4 5]  # <-- Missing commas between numbers

# ERROR 6: Invalid escape
path = "C:\Users\name"  # <-- Invalid escape sequence

# ERROR 7: Missing operator
x = 5
y = 10
z = x y  # <-- Missing operator between x and y

# ERROR 8: Invalid keyword
def test():
    brek  # <-- Misspelled 'break'

# ERROR 9: Unclosed bracket
data = [1, 2, 3, 4, 5  # <-- Missing closing bracket

# ERROR 10: Invalid assignment
5 = value  # <-- Can't assign to literal

# ERROR 11: Missing parentheses
length = len "hello"  # <-- Missing parentheses around argument

# ERROR 12: Invalid import
from math import squareroot  # <-- 'squareroot' doesn't exist, should be 'sqrt'

# ERROR 13: Multiple statements on one line
x = 5; y = 10; z = 15  # <-- Not an error, but style warning

# ERROR 14: Bare except
try:
    x = 1 / 0
except:  # <-- Bare except, should specify exception
    pass

# ERROR 15: Using '==' with None
if result == None:  # <-- Should be 'is None'
    pass

# This line is correct
print("Program completed")  # <-- This is correct