# Day 1: Variables and Data Types

> **Curriculum**: Python Basics | **Level**: beginner | **Time budget**: 30 min | **Goal**: get a job as a Python developer

## Learning Objectives

- Define what a variable is and explain why programs use them.
- Identify the four core Python data types: `int`, `float`, `str`, and `bool`.
- Write and run a Python statement that assigns a value to a variable.

## Concept Explanation

A variable is a named container that stores a value in your program's memory. Think of it like a labelled box: the label is the variable name, and whatever you put inside is the value.

In Python, you create a variable by writing its name, an equals sign, and a value:

```python
age = 25
name = "Alice"
price = 9.99
is_active = True
```

Python figures out the data type automatically based on what you assign. This is called dynamic typing. You do not need to declare the type upfront.

The four most common types are:

- **int** — whole numbers, positive or negative (e.g., `42`, `-7`)
- **float** — decimal numbers (e.g., `3.14`, `-0.5`)
- **str** — text wrapped in quotes (e.g., `"hello"`, `'world'`)
- **bool** — only two values: `True` or `False`

You can check a variable's type using the built-in `type()` function:

```python
print(type(age))     # <class 'int'>
print(type(name))    # <class 'str'>
print(type(price))   # <class 'float'>
print(type(is_active))  # <class 'bool'>
```

## Real-World Examples

**Example 1**: A shopping cart stores the item count as an `int` (`items = 3`) and the total price as a `float` (`total = 47.50`). Using the correct types ensures arithmetic works correctly.

**Example 2**: A login system stores a username as a `str` (`username = "alice123"`) and whether the user is logged in as a `bool` (`logged_in = False`). The bool drives conditional logic later.

**Example 3**: A weather app stores temperature as a `float` (`temperature = 23.5`) so it can handle decimal readings from sensors and display accurate values.

## Comprehension Questions

Answer each question in your own words before revealing the answer.

**Question 1**: What does Python do automatically when you write `score = 100`?

<details>
<summary>Show answer</summary>

Python creates a variable named `score`, assigns the integer value `100` to it, and stores it in memory. Python also infers the type as `int` without you specifying it.

</details>

**Question 2**: What is the difference between `42` and `42.0` in Python?

<details>
<summary>Show answer</summary>

`42` is an `int` (a whole number with no decimal component). `42.0` is a `float` (a number with a decimal point). They look similar but behave differently in some operations, such as division and type checking.

</details>

**Question 3**: Why would you use `True` or `False` instead of `1` or `0`?

<details>
<summary>Show answer</summary>

Using `True` and `False` (the `bool` type) makes your code more readable and communicates intent clearly. Boolean variables also work directly with `if` statements and logical operators, which makes the code easier to understand and maintain.

</details>

## Practical Tasks

### Core Task (15 to 30 min)

Open a Python interpreter or create a file called `day_01.py`. Write five variable assignments using at least three different data types. Print each variable and its type using `print()` and `type()`.

**Done when:**
- [ ] The script runs without errors.
- [ ] At least one variable uses `int`, one uses `str`, and one uses `float` or `bool`.
- [ ] Each variable's name clearly describes what it stores.

### Stretch Task (45 to 90 min)

Build a small personal profile program. Ask the user to input their name, age, and a fun fact about themselves. Store each input in a correctly typed variable. Print a formatted summary sentence using all three variables.

**Done when:**
- [ ] The program uses `input()` to collect all three values.
- [ ] The program converts age from `str` to `int` using `int()`.
- [ ] The program prints a sentence like: `"Hi, I'm Alice, I'm 25 years old, and I love hiking."`
- [ ] The script runs without errors on at least two different inputs.

## Further Reading

- *Python Crash Course* by Eric Matthes — Chapter 2 covers variables and data types with clear beginner examples.
- Documentation: "Python docs: Built-in Types" — the official reference for all Python types and their behaviour.
- Search: "Python variables and data types tutorial for beginners"
