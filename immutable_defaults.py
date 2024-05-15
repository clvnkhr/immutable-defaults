import inspect
import copy
from functools import wraps
from typing import Any, overload
from typing import Callable as F
from collections import defaultdict
from collections.abc import Iterable


class ImmutableDefaultsError(Exception):
    pass


@overload
def immutable_defaults[**P, T](_f: F[P, T]) -> F[P, T]: ...
@overload
def immutable_defaults[**P, T](
    *,
    ignore: Iterable[str] | None = None,
    deepcopy: bool | Iterable[str] = True,
) -> F[[F[P, T]], F[P, T]]: ...
def immutable_defaults[**P, T](
    _f: F[P, T] | None = None,
    *,
    ignore: Iterable[str] | None = None,
    deepcopy: bool | Iterable[str] = True,
) -> F[P, T] | F[[F[P, T]], F[P, T]]:
    """decorator to make a new (deep) copy of the original mutable defaults on every function call."""
    ignore = [] if ignore is None else ignore

    def dc1[U](_: str, v: U) -> U:
        return copy.deepcopy(v)

    def dc2[U](_: str, v: U) -> U:
        return copy.copy(v)

    if deepcopy is True:
        dc = dc1
    elif deepcopy is False:
        dc = dc2

    elif isinstance(deepcopy, Iterable):

        def dc3[U](k: str, v: U) -> U:
            if k in deepcopy:
                return copy.deepcopy(v)
            return copy.copy(v)

        dc = dc3

    else:
        raise ImmutableDefaultsError("deepcopy must be boolean or an iterable")

    def _immutable_defaults(f: F[P, T]) -> F[P, T]:
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
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
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

    @immutable_defaults
    def my_function(a: list = []):
        a.append("world")
        return a

    print(my_function())  # ['world']
    print(my_function(a=["hello"]))  # ['hello', 'world']
    print(my_function(["HELLO"]))  # ['HELLO', 'world']
    print(my_function())  #  ['world']

    @immutable_defaults(ignore=["b"])
    def my_function2(a=["hello"], b=[]):
        """basic function with ignore parameter"""
        a.append("world")
        b.append("!")
        return a + b

    print(my_function2())  # ['hello', 'world', '!']
    print(my_function2())  # ['hello', 'world', '!', '!']
    print(my_function2())  # ['hello', 'world', '!', '!', '!']

    # more exhaustive tests in tests/tests.py
