import unittest
from hypothesis import given, strategies as st
from immutable_defaults import immutable_defaults
import copy


# A sample function to test the decorator
@immutable_defaults
def append_to_list[T](value: T, my_list: list[T] = []):
    my_list.append(value)
    return my_list


# sample function with a mutable container accessible outside.
xs = []


@immutable_defaults
def append_to_xs(value, xs=xs):
    xs.append(value)
    return xs


class TestImmutableDefaults(unittest.TestCase):
    def test_append_to_list_with_default(self):
        # Test that the default list is not modified across function calls
        self.assertEqual(append_to_list(1), [1])
        self.assertEqual(append_to_list(2), [2])

    def test_append_to_list_with_provided_list(self):
        # Test that a provided list is used instead of the default
        custom_list = [100]
        self.assertEqual(append_to_list(1, custom_list), [100, 1])
        self.assertEqual(append_to_list(2, custom_list), [100, 1, 2])

    def test_append_to_xs_with_provided_list(self):
        # Test that the default list is not used even when passed in
        self.assertEqual(append_to_xs(1, xs), [1])
        self.assertEqual(append_to_list(2, xs), [2])


# Property-based tests using Hypothesis
class TestImmutableDefaultsHypothesis(unittest.TestCase):
    @given(st.integers(), st.lists(st.integers()))
    def test_append_to_list_property(self, value, custom_list):
        # Make a deep copy of the custom list to compare later
        original_list = copy.deepcopy(custom_list)
        result = append_to_list(value, custom_list)

        # Check that the result is the custom list with the value appended
        self.assertEqual(result, original_list + [value])

        # Call the function again with no list provided to ensure default is still empty
        self.assertEqual(append_to_list(value), [value])


if __name__ == "__main__":
    unittest.main()
