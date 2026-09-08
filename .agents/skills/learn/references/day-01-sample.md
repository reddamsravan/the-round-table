# Day 1: Variables and Mental Models

> **Curriculum**: Python Basics | **Level**: beginner | **Daily Target**: 30 min | **Goal**: Build reliable software

## Learning Objectives

- Explain how variables bind names to values in computer memory.
- Distinguish four primary data types: integers, floats, strings, and booleans.
- Predict program output before running code assignments.

## Core Mental Model

Think of a variable as a sticky note label. The label points to an object in memory.
You attach the name to data. When you change the variable, you move the label to a new value.

## Predict and Inquire

Read this sequence carefully before you check the answer:

```python
x = 10
y = x
x = 25
```

**Your Question:** What value does `y` hold after these three lines execute?

<details>
<summary>Check Your Prediction and Analysis</summary>

**Outcome:** `y` holds `10`, not `25`.
**Why:** Python evaluates the right side first. Line 2 binds `y` directly to `10`. Changing `x` on line 3 never affects `y`.

</details>

## Deep Dive and Applied Scenarios

Python infers data types automatically during assignment. Developers call this dynamic typing.
Four primary types appear in every program:

- **int**: Whole numbers such as `42` or `-7`.
- **float**: Decimal numbers such as `3.14` or `-0.5`.
- **str**: Text characters enclosed in quotes.
- **bool**: Binary flags with only two states: `True` or `False`.

### Case Study 1: Shopping Cart
A checkout system tracks item counts with integers. It stores total prices as floats. It tracks checkout status with a boolean flag.

### Case Study 2: Weather Sensor
A weather station records location names as strings. It samples temperature readings as floats. It flags hardware alerts as booleans.

## Common Misconceptions and Traps

### Pitfall 1: Equal Sign Means Algebraic Equality
- **The Trap:** Beginners think `x = x + 1` is impossible math.
- **The Reality:** The single equals sign means assignment. Python computes the right side first. It then saves the result into the label on the left.

### Pitfall 2: Confusing Types in Arithmetic
- **The Trap:** Adding `"5" + "5"` expects `10`.
- **The Reality:** Python treats quoted numbers as strings. It joins them into `"55"`. Always convert strings with `int()` before math.

## Comprehension Self-Check

Answer each question in your own words before revealing the answer.

**Question 1:** What happens during variable assignment?

<details>
<summary>Show Answer</summary>

Python creates the value in memory. It then binds your variable name to that memory location.

</details>

**Question 2:** How do 42 and 42.0 differ?

<details>
<summary>Show Answer</summary>

The integer `42` stores whole numbers. The float `42.0` stores fractional numbers with decimal precision.

</details>

**Question 3:** Why should you use booleans instead of numbers?

<details>
<summary>Show Answer</summary>

Booleans clarify intent. They express binary state directly and reduce confusion in conditional checks.

</details>

## Practical Tasks

### Tier 1: Analyze and Critique (5 to 10 min)
Examine this broken snippet: `total = "40" + 2`. Explain why Python raises a TypeError and write the correct expression.

**Done when:**
- [ ] You identified the string and integer mismatch.
- [ ] You wrote the corrected expression using `int("40") + 2`.

### Tier 2: Core Application (15 to 30 min)
Write a script that defines four variables covering int, float, str, and bool. Print each variable with its type name.

**Done when:**
- [ ] The script runs without errors.
- [ ] The script assigns values for all four core data types.
- [ ] Output displays clear labels for each variable and type.

### Tier 3: Stretch Transfer (30 to 60 min)
Reassign a single variable name through three different data types sequentially. Print the identity and type at each step.

**Done when:**
- [ ] You verified how Python rebinds names in memory.
- [ ] You documented why dynamic typing requires testing vigilance.

## Further Exploration

- **Authoritative Source**: Python Language Reference, Chapter 3 on Data Model.
- **Search Query**: Python variable naming conventions PEP 8.
- **Deep Thought Prompt**: Why does Python treat integers as immutable objects?
