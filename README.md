# immutable_defaults

[![tests](https://github.com/clvnkhr/immutable-defaults/actions/workflows/python-package.yml/badge.svg)](https://github.com/clvnkhr/immutable-defaults/actions/workflows/python-package.yml)

Simple decorator to force immutability to function arguments by deepcopying. Never again pass `None` when your heart wants to pass an empty list. Also works for arbitrary objects that can be deepcopied. Has simple config options for granularity or performance (copy vs deepcopy).

No dependencies.

In order to use various type hints we require Python >=3.12.

## How to install

`pip install immutable-defaults` or your equivalent (e.g. `pdm add immutable-defaults`)

## Example usage

```python
from immutable_defaults import immutable_defaults 

@immutable_defaults
def my_function(a: list = []):
    a.append("world")
    return a

print(my_function())  # ['world']
print(my_function(a=["hello"]))  # ['hello', 'world']
print(my_function(["HELLO"]))  # ['HELLO', 'world']
print(my_function())  #  ['world']

@immutable_defaults(ignore=["b"])
def my_function2(a = ["hello"], b = []):
    """basic function with ignore parameter"""
    a.append("world")
    b.append("!")
    return a + b

print(my_function2())  # ['hello', 'world', '!']
print(my_function2())  # ['hello', 'world', '!', '!']
print(my_function2())  # ['hello', 'world', '!', '!', '!']

# more exhaustive tests in tests/tests.py
```

### Methods, Classmethods, and Staticmethods

The decorator works with methods, classmethods and staticmethods. Since `@immutable_defaults` requires that the wrapped function is `callable`, make sure that the outer decorator is `@classmethod`/`@staticmethod`.

## Optional keyword arguments

- `@immutable_defaults` can be called with keyword arguments `deepcopy` and `ignore`.
- `deepcopy: boolean | Iterable[str] = True`
  - if `True` then defaults are copied with `copy.deepcopy`. If False, then with `copy.copy`.
  - If passed an iterable of argument names then those arguments will be deep copied and other mutable defaults will be shallow copied, e.g. in the below `a` and `arg` will be deep copied while `b` will be shallow copied.

  ```python
    @immutable_defaults(deepcopy=["a","arg"]) 
    def f(a=[[1]], b=[], arg={1: {2}}): ...
  ```
  
- `ignore: Iterable[str] | None = None`
  - all argument names passed will have the default Python behavior.

## Input validation

- We check that you cannot have the same mutable object (as per `a is b` comparison) marked for both shallow and deep copying. For example, the below will raise an `ImmutableDefaultsError`:

```python
xss = [[1]]
@immutable_defaults(deepcopy=["xss2"]) # raises ImmutableDefaultsError
def f(x, xss1 = xss, xss2 = xss): ...
```

- Similarly, we check that you cannot ignore and not ignore the same mutable object. For example, the below will raise an `ImmutableDefaultsError`:

```python
xss = [[1]]
@immutable_defaults(ignore=["xss2"]) # raises ImmutableDefaultsError
def f(x, xss1 = xss, xss2 = xss): ...
```

- A `KeyError` is raised if either `deepcopy` or `ignore` have arguments that cannot be found in the signature of the decorated function.
  - It would have been easy to silently do nothing when variables in `ignore` are not present, but this would make typos very hard to debug.
- `ignore` takes precedence over `deepcopy`, i.e. `@immutable_defaults(ignore=["x"], deepcopy=["x"])` will do the same thing as `@immutable_defaults(ignore=["x"])`

## Prior art

(Comments valid May 13 2024)

- comparison with <https://pypi.org/project/immutable_default_args/>
  - we deep copy all defaults except for standard immutable types (int, float, complex, bool, str, tuple, frozenset). This means we cover sets, and also other custom mutable objects that implement `__deepcopy__` (or optionally `__copy__`).
  - Instead of a metaclass, we have a class decorator.
- comparison with <https://pypi.org/project/python-immutable/>
- comparison with <https://github.com/roodrepo/default_mutable/>
  - we have typed code and IMO better naming.
- comparison with <https://pypi.org/project/python-none-objects/>
  - completely different solution to the mutable default arguments problem.
  - only works for empty containers.

## Todo

- Performance benchmarking - what is the overhead?
- Make publishing to pypi part of github workflow
