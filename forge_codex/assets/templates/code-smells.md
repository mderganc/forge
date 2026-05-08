# Code Smells Catalog

Based on Martin Fowler and Kent Beck's catalog. Used by the architect and critic during code review (architecture mode) and evaluate review mode to identify symptoms of deeper design problems.

## Core Principle

> A code smell is not a bug — it's a surface indicator of a design problem. Every smell has a specific refactoring remedy. Identify the smell, confirm the underlying issue, then apply the targeted fix.

## Smell Catalog

### Bloaters — Code that has grown too large

| Smell | Recognition | Refactoring | Severity |
|-------|------------|-------------|----------|
| **Long Method** | Method > 20 lines, does multiple things, needs comments to explain sections | Extract Method, Replace Temp with Query | warning |
| **Large Class** | Class > 300 lines, has many fields, multiple responsibilities | Extract Class, Extract Subclass | warning |
| **Long Parameter List** | Method takes > 3 parameters | Introduce Parameter Object, Preserve Whole Object | suggestion |
| **Data Clumps** | Same group of fields/parameters appears together in multiple places | Extract Class, Introduce Parameter Object | warning |
| **Primitive Obsession** | Uses primitives instead of small objects (money as float, phone as string) | Replace Data Value with Object, Replace Type Code with Class | suggestion |

### Object-Orientation Abusers — Misuse of OO mechanisms

| Smell | Recognition | Refactoring | Severity |
|-------|------------|-------------|----------|
| **Switch Statements** | Repeated switch/if-else on same type field across methods | Replace Conditional with Polymorphism | suggestion |
| **Refused Bequest** | Subclass uses little of its parent's behavior | Replace Inheritance with Delegation, Extract Subclass | warning |
| **Parallel Inheritance** | Creating a subclass in one hierarchy requires a subclass in another | Move Method, Move Field to collapse hierarchies | warning |
| **Alternative Classes with Different Interfaces** | Two classes do the same thing with different method names | Rename Method, Extract Interface | suggestion |

### Change Preventers — Code that makes changes expensive

| Smell | Recognition | Refactoring | Severity |
|-------|------------|-------------|----------|
| **Divergent Change** | One class modified for many different reasons (multiple axes of change) | Extract Class (one per axis of change) | warning |
| **Shotgun Surgery** | One logical change requires modifying many classes | Move Method/Field, Inline Class to consolidate | critical |
| **Feature Envy** | Method uses another class's data more than its own | Move Method to the class it envies | warning |

### Dispensables — Code that adds no value

| Smell | Recognition | Refactoring | Severity |
|-------|------------|-------------|----------|
| **Dead Code** | Unreachable code, unused variables, unused parameters, unused imports | Safe Delete | warning |
| **Speculative Generality** | Unused abstractions, interfaces with one implementor, unused parameters "for the future" | Collapse Hierarchy, Inline Class, Remove Parameter | suggestion |
| **Comments as Deodorant** | Comments explaining WHAT code does (not WHY) — indicates unclear code | Extract Method (name it what the comment says), Rename | suggestion |

### Couplers — Code that creates excessive coupling

| Smell | Recognition | Refactoring | Severity |
|-------|------------|-------------|----------|
| **Inappropriate Intimacy** | Classes access each other's private internals, circular references | Move Method/Field, Extract Class, Hide Delegate | critical |
| **Message Chains** | `a.getB().getC().getD()` — long chains coupling caller to structure | Hide Delegate, Extract Method | warning |
| **Middle Man** | Class delegates most methods to another class, adding no value | Remove Middle Man, Inline Method | suggestion |
| **God Class** | One class knows everything, controls everything, has most of the logic | Extract Class repeatedly until SRP is met | critical |

## How to Use This Catalog

### During Code Review (Architecture Mode)

1. Scan changed files for the top 5 high-severity smells: God Class, Shotgun Surgery, Inappropriate Intimacy, Feature Envy, Long Method
2. For each smell found:
   - Cite the specific location (file:line)
   - Name the smell
   - State the consequence ("this means changing X requires touching Y, Z, and W")
   - Recommend the specific refactoring
3. Only flag smells in code that was changed or is directly adjacent to changes

### During Evaluate Review

1. Check the full codebase for systemic smell patterns (are God Classes proliferating?)
2. Check if the implementation introduced new smells
3. Check if the implementation resolved existing smells

## Rules

1. **Smells are not always bugs.** A method that's 25 lines but doing one clear thing is fine. Use judgment.
2. **Context matters.** A long parameter list in a public API might be intentional. A long parameter list in an internal helper is a smell.
3. **Don't refactor what you didn't change.** Flag the smell, recommend the fix, but don't expand scope unless asked.
4. **Severity escalates with repetition.** One Feature Envy instance is a suggestion. Five instances of the same pattern is a warning. A systemic pattern is critical.
