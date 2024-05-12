import inspect
import copy
from functools import wraps
from typing import Any, Callable, TypeVar, overload
from typing_extensions import ParamSpec
from collections import defaultdict
from collections.abc import Iterable

T = TypeVar("T")
U = TypeVar("U")
P = ParamSpec("P")
F = Callable[P, T]


class ImmutableDefaultsError(Exception):
    pass


@overload
def immutable_defaults(__f: F) -> F: ...
@overload
def immutable_defaults(
    *, ignore: Iterable[str] | None = None, deepcopy: bool | Iterable[str] = True
) -> Callable[[F], F]: ...
def immutable_defaults(
    _f: F | None = None,
    *,
    ignore: Iterable[str] | None = None,
    deepcopy: bool | Iterable[str] = True,
):
    """decorator to make a new (deep) copy of the original mutable defaults on every function call."""
    ignore = [] if ignore is None else ignore

    if deepcopy is True:

        def dc(_: str, v: U) -> U:  # type: ignore
            return copy.deepcopy(v)

    elif deepcopy is False:

        def dc(_: str, v: U) -> U:  # type: ignore
            return copy.copy(v)

    elif isinstance(deepcopy, Iterable):

        def dc(k: str, v: U) -> U:  # type: ignore
            if k in deepcopy:
                return copy.deepcopy(v)
            return copy.copy(v)

    else:
        raise ImmutableDefaultsError("deepcopy must be boolean or a list")

    def _immutable_defaults(f: F) -> F:
        # keep a copy of the defaults outside of the wrapped function
        immut_types: tuple = (int, float, complex, bool, str, tuple, frozenset)
        sig: inspect.Signature = inspect.signature(f)
        func_defaults: dict[str, Any] = {
            k: v.default
            for k, v in sig.parameters.items()
            # k in ignore is removed to speed up function execution,
            # but only after we check that there are no ArgumentErrors
            if v.default is not inspect.Parameter.empty
            and not isinstance(v, immut_types)
        }

        # check if have deepcopy or ignore settings conflict
        if isinstance(deepcopy, Iterable) or isinstance(ignore, Iterable):
            mut_tracker: defaultdict[Any, list[str]] = defaultdict(list)
            for k in func_defaults:
                mut_tracker[id(func_defaults[k])].append(k)

            if isinstance(deepcopy, Iterable):
                # assume that elements in deepcopy are unique
                for arg in deepcopy:
                    if any(
                        arg2 not in deepcopy
                        for arg2 in mut_tracker[id(func_defaults[arg])]
                    ):
                        raise ImmutableDefaultsError(
                            f"default argument for {arg} can be both shallow and deepcopied"
                        )

            # repeat for ignore list
            if isinstance(ignore, Iterable):
                for arg in ignore:
                    if any(
                        arg2 not in ignore
                        for arg2 in mut_tracker[id(func_defaults[arg])]
                    ):
                        raise ImmutableDefaultsError(
                            f"default argument for {arg} is both ignored and set to immutable"
                        )
                # clean up func_defaults to speed up execution
                for arg in ignore:
                    del func_defaults[arg]

        @wraps(f)
        def wrapped(*args, **kwargs):
            # Idea:
            # 1. bind_partial the args and kwargs given at call site, store in bound_args
            # 2. manually deep copy each default into bound_args.arguments
            #       - this prevents the actual default of func from being used
            # 3. call the function with the modified bound_args

            bound_args: inspect.BoundArguments = sig.bind_partial(*args, **kwargs)
            for arg, default_value in func_defaults.items():
                if (
                    arg not in bound_args.arguments
                    or bound_args.arguments[arg]
                    is default_value  # if the default value is passed in, deepcopy it anyway
                ):
                    bound_args.arguments[arg] = dc(arg, default_value)

            # Call the original function with the new arguments
            # NB .args and .kwargs are views into .arguments
            return f(*bound_args.args, **bound_args.kwargs)

        return wrapped

    if _f is None:
        return _immutable_defaults
    return _immutable_defaults(_f)


if __name__ == "__main__":
    # Example usage
    @immutable_defaults
    def my_function(a, b, c: list = []):
        """basic function"""
        c.append("world")
        return a, b, c

    print(my_function(1, 2))  ############## (1, 2, ['world'])
    print(my_function(2, 6, c=["hello"]))  # (2, 6, ['hello', 'world'])
    print(my_function(3, 9, ["HELLO"]))  ### (3, 9, ['HELLO', 'world'])
    print(my_function(1, 2))  ############## (1, 2, ['world'])

    @immutable_defaults(ignore=["c"])
    def my_function2(a, b, c: list = []):
        """basic function with ignore parameter"""
        c.append("world")
        return a, b, c

    print(my_function2(1, 2))  # (1, 2, ['world'])
    print(my_function2(1, 3))  # (1, 3, ['world', 'world'])
    print(my_function2(1, 4))  # (1, 4, ['world', 'world', 'world'])

    # more exhaustive tests in tests/tests.py
