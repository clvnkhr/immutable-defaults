import unittest
from hypothesis import given, strategies as st
from immutable_defaults import immutable_defaults, ImmutableDefaultsError
from typing import TypeVar, cast
import copy

T = TypeVar("T")
U = TypeVar("U")


# sample function with immutable default (checking that behavior is not changed)
@immutable_defaults
def add(x: int, y: int = 1):
    return x + y


# sample functions to test the decorator with lists, sets, dicts
@immutable_defaults
def append_to_list(value: T, my_list: list[T] = []) -> list[T]:
    my_list.append(value)
    return my_list


@immutable_defaults
def add_to_set(value: T, my_set: set[T] = set()) -> set[T]:
    my_set.add(value)
    return my_set


@immutable_defaults
def add_kv_to_dict(k: T, v: U, my_dict: dict[T, U] = {}) -> dict[T, U]:
    my_dict[k] = v
    return my_dict


# sample function with a mutable container that is accessible outside.
default_xs: list[int] = [42]


@immutable_defaults
def append_to_xs(value, xs=default_xs):
    xs.append(value)
    return xs


class TestImmutableDefaults(unittest.TestCase):
    def test_append_to_list_with_default(self) -> None:
        # Test that the default list is not modified across function calls
        self.assertEqual(append_to_list(1), [1])
        self.assertEqual(append_to_list(2), [2])

    def test_append_to_list_with_provided_list(self) -> None:
        # Test that a provided list is used instead of the default
        custom_list: list[int] = [100]
        self.assertEqual(append_to_list(1, custom_list), [100, 1])
        self.assertEqual(append_to_list(2, custom_list), [100, 1, 2])

    def test_append_to_xs_with_provided_list(self) -> None:
        # Test that the default list is not used even when passed in
        self.assertEqual(append_to_xs(1), default_xs + [1])
        self.assertEqual(append_to_xs(2), default_xs + [2])
        self.assertEqual(append_to_xs(1, default_xs), default_xs + [1])
        self.assertEqual(append_to_xs(3, default_xs), default_xs + [3])

    def test_default_copy_is_deepcopy(self) -> None:
        xss: list[list[int | str | float]] = [[1], ["two"], [3.1]]

        @immutable_defaults
        def inner_append(x, xss=xss):
            for xs in xss:
                xs.append(x)
            return xss

        self.assertEqual(inner_append(42), [[1, 42], ["two", 42], [3.1, 42]])
        self.assertEqual(inner_append(42), [[1, 42], ["two", 42], [3.1, 42]])

    def test_deepcopy_false_means_shallow_copy(self) -> None:
        xss: list[list[int | str | float]] = [[1], ["two"], [3.1]]

        @immutable_defaults(deepcopy=False)
        def inner_append_nodeep(x, xss=xss):
            xss.append([])
            for xs in xss:
                xs.append(x)
            return xss

        self.assertEqual(
            inner_append_nodeep(42), [[1, 42], ["two", 42], [3.1, 42], [42]]
        )
        self.assertEqual(
            inner_append_nodeep(1), [[1, 42, 1], ["two", 42, 1], [3.1, 42, 1], [1]]
        )
        self.assertIsNot(inner_append_nodeep(-1), xss)

    def test_deepcopy_false_shallow_copy_enough_for_list(self) -> None:
        @immutable_defaults(deepcopy=False)
        def append_to_list2(value: T, my_list: list[T] = []) -> list[T]:
            my_list.append(value)
            return my_list

        self.assertEqual(append_to_list2(1), [1])
        self.assertEqual(append_to_list2(2), [2])

    def test_deepcopy_list_restriction_works(self) -> None:
        xss1: list[list[int | str]] = [[1], ["two"]]
        xss2: list[list[int | str]] = [[3], ["four"]]
        # NOTE: compare with test below

        @immutable_defaults(deepcopy=["xss2"])
        def inner_append_shallow_deep(
            x: int | str,
            xss1: list[list[int | str]] = xss1,
            xss2: list[list[int | str]] = xss2,
        ) -> tuple[list[list[int | str]], list[list[int | str]]]:
            for xs in xss1:
                xs.append(x)
            for xs in xss2:
                xs.append(x)
            return (xss1, xss2)

        self.assertEqual(
            inner_append_shallow_deep(-1),
            ([[1, -1], ["two", -1]], [[3, -1], ["four", -1]]),
        )
        self.assertEqual(
            inner_append_shallow_deep(-2),
            ([[1, -1, -2], ["two", -1, -2]], [[3, -2], ["four", -2]]),
        )

    def test_detects_deep_and_shallow_copying(self) -> None:
        xss: list[list[int | str]] = [[1], ["two"]]
        with self.assertRaises(ImmutableDefaultsError) as e_ctx:

            @immutable_defaults(deepcopy=["xss2"])
            def inner_append_shallow_deep(
                x: int | str,
                xss1: list[list[int | str]] = xss,
                xss2: list[list[int | str]] = xss,
            ) -> tuple[list[list[int | str]], list[list[int | str]]]:
                for xs in xss1:
                    xs.append(x)
                for xs in xss2:
                    xs.append(x)
                return (xss1, xss2)

            inner_append_shallow_deep(1)

        e: str = cast(str, e_ctx.exception.args[0]).casefold()
        self.assertTrue(
            "shallow" in e and "deep" in e
        )  # fuzzy test for assertion message

    def test_detects_ignore_and_immutable(self) -> None:
        xss: list[list[int | str]] = [[1], ["two"]]
        with self.assertRaises(ImmutableDefaultsError) as e_ctx:

            @immutable_defaults(ignore=["xss2"])
            def inner_append_shallow_deep(
                x: int | str,
                xss1: list[list[int | str]] = xss,
                xss2: list[list[int | str]] = xss,
            ) -> tuple[list[list[int | str]], list[list[int | str]]]:
                for xs in xss1:
                    xs.append(x)
                for xs in xss2:
                    xs.append(x)
                return (xss1, xss2)

            inner_append_shallow_deep(1)

        e = e_ctx.exception.args[0]
        self.assertTrue("ignore" in e)  # fuzzy test for assertion message

    def test_no_error_with_similar_but_distinct_args_where_one_is_shallow(self) -> None:
        xss: list[list[int]] = [[0], [1]]

        @immutable_defaults(deepcopy=["xss1"])
        def inner_append_shallow_deep(
            x: int,
            xss1: list[list[int]] = xss,
            xss2: list[list[int]] = copy.deepcopy(xss),
        ) -> tuple[list[list[int]], list[list[int]]]:
            for xs in xss1:
                xs.append(x)
            for xs in xss2:
                xs.append(x)
            return (xss1, xss2)

        out1, out2 = inner_append_shallow_deep(-1)
        self.assertEqual(out1, out2)
        out3, out4 = inner_append_shallow_deep(-2)
        self.assertNotEqual(out3, out4)

    def test_no_error_with_similar_but_distinct_args_where_one_is_ignore(self) -> None:
        xss: list[list[int]] = [[0], [1]]

        @immutable_defaults(ignore=["xss1"])
        def inner_append_shallow_deep(
            x: int,
            xss1: list[list[int]] = xss,
            xss2: list[list[int]] = copy.deepcopy(xss),
        ) -> tuple[list[list[int]], list[list[int]]]:
            for xs in xss1:
                xs.append(x)
            for xs in xss2:
                xs.append(x)
            return (xss1, xss2)

        out1, out2 = inner_append_shallow_deep(-1)
        self.assertEqual(out1, out2)
        out3, out4 = inner_append_shallow_deep(-2)
        self.assertNotEqual(out3, out4)

    def test_does_not_silently_fail_when_ignore_list_is_wrong(self) -> None:
        with self.assertRaises(KeyError):

            @immutable_defaults(ignore=["missing"])
            def func() -> None:
                pass

            func()

    def test_does_not_silently_fail_when_deepcopy_list_is_wrong(self) -> None:
        with self.assertRaises(KeyError):

            @immutable_defaults(deepcopy=["missing"])
            def func() -> None:
                pass

            func()

    def test_func_with_variable_kwargs(self):
        # Test that the function accepts variable keyword arguments

        @immutable_defaults
        def func_with_kwargs(**kwargs):
            return kwargs

        result = func_with_kwargs(a=1, b=2, c=3)
        self.assertEqual(result, {"a": 1, "b": 2, "c": 3})

    def test_func_with_custom_class_default(self):
        # Test that the default is deepcopied when it is an instance of a CustomClass
        class CustomClass[T]:
            def __init__(self, value: T):
                self.value: T = value

            def __deepcopy__(self, memo):
                return CustomClass(copy.deepcopy(self.value, memo))

        init: list[list[int]] = [[10]]

        @immutable_defaults
        def func_with_custom_default(
            custom=CustomClass(init),
        ) -> CustomClass:
            custom.value[0].append(1)
            return custom

        self.assertEqual(func_with_custom_default().value, [[10, 1]])
        self.assertEqual(func_with_custom_default().value, [[10, 1]])

        def func_with_custom_default2(
            custom=CustomClass(init),
        ) -> CustomClass:
            custom.value[0].append(1)
            return custom

        self.assertEqual(func_with_custom_default2().value, [[10, 1]])
        self.assertNotEqual(func_with_custom_default2().value, [[10, 1]])

    def test_idempotence(self) -> None:
        @immutable_defaults
        @immutable_defaults
        def append(x: int, to: list[int] = []) -> list[int]:
            to.append(x)
            return to

        self.assertEqual(append(1), [1])
        self.assertEqual(append(1), [1])

    def test_idempotence_5(self) -> None:
        @immutable_defaults
        @immutable_defaults
        @immutable_defaults
        @immutable_defaults
        @immutable_defaults
        def append(x: int, to: list[int] = []) -> list[int]:
            to.append(x)
            return to

        self.assertEqual(append(1), [1])
        self.assertEqual(append(1), [1])

    def test_idempotence_100(self) -> None:
        def append(x: int, to: list[int] = []) -> list[int]:
            to.append(x)
            return to

        for __ in range(100):
            append = immutable_defaults(append)

        self.assertEqual(append(1), [1])
        self.assertEqual(append(1), [1])

    def test_ignore_with_double_decorator1(self) -> None:
        @immutable_defaults(ignore=["to"])
        @immutable_defaults
        def append1(x: int, to: list[int] = []) -> list[int]:
            to.append(x)
            return to

        self.assertEqual(append1(1), [1])
        self.assertEqual(append1(1), [1])

    def test_ignore_with_double_decorator2(self) -> None:
        @immutable_defaults
        @immutable_defaults(ignore=["to"])
        def append1(x: int, to: list[int] = []) -> list[int]:
            to.append(x)
            return to

        self.assertEqual(append1(1), [1])
        self.assertEqual(append1(1), [1])

    def test_ignore_with_double_decorator3(self) -> None:
        @immutable_defaults(ignore=["to"])
        @immutable_defaults(ignore=["to"])
        def append1(x: int, to: list[int] = []) -> list[int]:
            to.append(x)
            return to

        self.assertEqual(append1(1), [1])
        self.assertEqual(append1(1), [1, 1])

    # Property-based tests
    @given(st.integers(), st.integers())
    def test_integer_default_still_works(self, x, y) -> None:
        """verify no change in behavior after decorating function without mutable defaults"""
        self.assertEqual(x + 1, add(x))
        self.assertEqual(x + y, add(x, y))
        self.assertEqual(x + y, add(x, y=y))

    @given(st.integers())
    def test_append_to_list_copies_default(self, x) -> None:
        self.assertEqual(append_to_list(x), [x])
        self.assertEqual(append_to_list(x), [x])

    @given(st.integers(), st.integers())
    def test_append_to_list_with_arg_still_works(self, x, y) -> None:
        self.assertEqual(append_to_list(x, [y]), [y, x])
        self.assertEqual(append_to_list(x, my_list=[y]), [y, x])
        # nb order of x and y is important
        # verify the default behavior still works
        self.assertEqual(append_to_list(x), [x])

    @given(st.integers(), st.integers())
    def test_add_to_set_copies_default(self, x, y) -> None:
        self.assertEqual(add_to_set(x), {x})
        self.assertEqual(add_to_set(x), {x})

    @given(st.integers(), st.integers())
    def test_add_to_set_with_arg_still_works(self, x, y) -> None:
        self.assertEqual(add_to_set(x, {y}), {y, x})
        self.assertEqual(add_to_set(x, my_set={y}), {y, x})
        # verify the default behavior still works
        self.assertEqual(add_to_set(x), {x})

    @given(st.integers(), st.integers())
    def test_add_kv_to_dict_copies_default(self, k, v) -> None:
        self.assertEqual(add_kv_to_dict(k, v), {k: v})
        self.assertEqual(add_kv_to_dict(k, v), {k: v})

    @given(st.integers(), st.integers(), st.integers(), st.integers())
    def test_add_kv_to_dict_still_works(self, k, v, kk, vv) -> None:
        self.assertEqual(add_kv_to_dict(k, v, {kk: vv}), {kk: vv, k: v})
        self.assertEqual(add_kv_to_dict(k, v, my_dict={kk: vv}), {kk: vv, k: v})
        # nb if {kk: vv, k: v} in above line is replaced with {k:v, kk: vv} test will fail
        # since second key val assignment can override when k=kk
        self.assertEqual(add_kv_to_dict(k, v), {k: v})

    def test_decorator_on_method(self) -> None:
        class MyClass:
            @immutable_defaults
            def append(self, x, to=[]):
                to.append(x)
                return to

        my_class = MyClass()
        self.assertEqual(my_class.append(5), [5])
        self.assertEqual(my_class.append(1), [1])

    def test_decorator_on_classmethod1(self) -> None:
        class MyClass:
            @classmethod
            @immutable_defaults
            def append(cls, x, to=[]):
                to.append(x)
                return to

        self.assertEqual(MyClass.append(5), [5])
        self.assertEqual(MyClass.append(1), [1])
        my_class = MyClass()
        self.assertEqual(my_class.append(5), [5])
        self.assertEqual(my_class.append(1), [1])

    def test_decorator_on_staticmethod1(self) -> None:
        class MyClass:
            @staticmethod
            @immutable_defaults
            def append(x, to=[]):
                to.append(x)
                return to

        self.assertEqual(MyClass.append(5), [5])
        self.assertEqual(MyClass.append(1), [1])
        my_class = MyClass()
        self.assertEqual(my_class.append(5), [5])
        self.assertEqual(my_class.append(1), [1])


if __name__ == "__main__":
    unittest.main()
