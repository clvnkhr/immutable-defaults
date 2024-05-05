import inspect
from copy import deepcopy
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def immutable_defaults(f: Callable[..., T]):
    """decorator to make a new copy of the original mutable defaults on every function call."""

    # keep a copy of the defaults outside of the wrapped function
    sig: inspect.Signature = inspect.signature(f)
    func_defaults: dict[str, Any] = {
        k: v.default
        for k, v in sig.parameters.items()
        if v.default is not inspect.Parameter.empty
    }

    @wraps(f)
    def wrapped(*args, **kwargs) -> T:
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
                is default_value  # if somehow the default value is passed in, forbid it anyway
            ):
                bound_args.arguments[arg] = deepcopy(default_value)

        # Call the original function with the new arguments
        # NB .args and .kwargs are views into .arguments
        return f(*bound_args.args, **bound_args.kwargs)

    return wrapped


if __name__ == "__main__":
    # Example usage
    @immutable_defaults
    def my_function(a, b, c: list = []):
        """Hello world"""
        c.append("world")
        return a, b, c

    print(my_function(1, 2))
    print(my_function(2, 6, c=["hello"]))
    print(my_function(3, 9, ["HELLO"]))
    print(my_function(1, 2))
