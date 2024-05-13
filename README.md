# immutable-defaults-py

- comparison with <https://pypi.org/project/immutable_default_args/>
  - we deep copy all defaults except for standard immutable types (int, float, complex, bool, str, tuple, frozenset). This means we covers sets, and also other custom mutable containers
- comparison with <https://github.com/roodrepo/default_mutable/tree/v0-dev>
  - we do not have a metaclass that auto-applies to all methods
  - we have fully typed code
- comparison with <https://pypi.org/project/python-none-objects/>
  - completely different implementation
  - only works for empty containers
- lots of tests
<https://pypi.org/project/python-immutable/>

# Usage

## todo
