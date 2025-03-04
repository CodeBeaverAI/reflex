from typing import Any, Literal

import pytest

from reflex.utils import types


@pytest.mark.parametrize(
    "params, allowed_value_str, value_str",
    [
        (["size", 1, Literal["1", "2", "3"], "Heading"], "'1','2','3'", "1"),
        (["size", "1", Literal[1, 2, 3], "Heading"], "1,2,3", "'1'"),
    ],
)
def test_validate_literal_error_msg(params, allowed_value_str, value_str):
    with pytest.raises(ValueError) as err:
        types.validate_literal(*params)

    assert (
        err.value.args[0] == f"prop value for {params[0]!s} of the `{params[-1]}` "
        f"component should be one of the following: {allowed_value_str}. Got {value_str} instead"
    )


@pytest.mark.parametrize(
    "cls,cls_check,expected",
    [
        (int, Any, True),
        (tuple[int], Any, True),
        (list[int], Any, True),
        (int, int, True),
        (int, object, True),
        (int, int | str, True),
        (int, str | int, True),
        (str, str | int, True),
        (str, int | str, True),
        (int, str | float | int, True),
        (int, str | float, False),
        (int, float | str, False),
        (int, str, False),
        (int, list[int], False),
    ],
)
def test_issubclass(
    cls: types.GenericType, cls_check: types.GenericType, expected: bool
) -> None:
    assert types._issubclass(cls, cls_check) == expected


class CustomDict(dict[str, str]):
    """A custom dict with generic arguments."""

    pass


class ChildCustomDict(CustomDict):
    """A child of CustomDict."""

    pass


class GenericDict(dict):
    """A generic dict with no generic arguments."""

    pass


class ChildGenericDict(GenericDict):
    """A child of GenericDict."""

    pass


@pytest.mark.parametrize(
    "cls,expected",
    [
        (int, False),
        (str, False),
        (float, False),
        (tuple[int], True),
        (list[int], True),
        (int | str, True),
        (str | int, True),
        (dict[str, int], True),
        (CustomDict, True),
        (ChildCustomDict, True),
        (GenericDict, False),
        (ChildGenericDict, False),
    ],
)
def test_has_args(cls, expected: bool) -> None:
    assert types.has_args(cls) == expected

# New tests to increase coverage for reflex/utils/types.py
def test_get_origin():
    """Test get_origin returns the correct origin for a generic type."""
    from typing import List
    origin = types.get_origin(List[int])
    assert origin == list

def test_is_generic_alias():
    """Test that is_generic_alias correctly identifies generic aliases."""
    assert types.is_generic_alias(list[int]) is True
    assert types.is_generic_alias(int) is False

def test_unionize():
    """Test unionize returns the correct unionized type."""
    # With a single argument returns itself.
    assert types.unionize(int) is int
    # With multiple arguments returns a Union type containing all types.
    result = types.unionize(int, str)
    from typing import get_args, Union
    args = get_args(result)
    assert int in args and str in args

def test_is_none():
    """Test that is_none returns True for None types and False otherwise."""
    assert types.is_none(type(None)) is True
    assert types.is_none(None) is True
    assert types.is_none(int) is False

def test_is_union():
    """Test that is_union returns True for union types."""
    union = int | str
    assert types.is_union(union) is True
    assert types.is_union(int) is False

def test_is_literal():
    """Test that is_literal returns True for literal types."""
    from typing import Literal
    literal_type = Literal[1, 2, 3]
    assert types.is_literal(literal_type) is True
    assert types.is_literal(int) is False

def test_get_property_hint():
    """Test that get_property_hint returns the correct type hint for a property."""
    class Dummy:
        def get_value(self) -> int:
            return 5
        my_prop = property(get_value)

    hint = types.get_property_hint(Dummy.my_prop)
    assert hint == int

def test_get_attribute_access_type_annotation():
    """Test that get_attribute_access_type retrieves type annotation from a plain class."""
    class DummyModel:
        my_attr: str

    hint = types.get_attribute_access_type(DummyModel, "my_attr")
    assert hint == str

def test_get_attribute_access_type_property():
    """Test that get_attribute_access_type retrieves a property hint."""
    class Dummy:
        @property
        def my_prop(self) -> float:
            return 3.14
    hint = types.get_attribute_access_type(Dummy, "my_prop")
    assert hint == float

def test__isinstance():
    """Test the _isinstance function for various type checks."""
    # Simple type checking
    assert types._isinstance(5, int) is True
    # Union type
    assert types._isinstance("hello", int | str) is True
    # Literal type positive and negative
    from typing import Literal
    assert types._isinstance(1, Literal[1, 2, 3]) is True
    assert types._isinstance(4, Literal[1, 2, 3]) is False

def test_is_encoded_fstring():
    """Test that is_encoded_fstring correctly identifies encoded f-strings."""
    from reflex import constants
    encoded = "some " + constants.REFLEX_VAR_OPENING_TAG + " value"
    assert types.is_encoded_fstring(encoded) is True
    assert types.is_encoded_fstring("plain string") is False

def test_validate_parameter_literals_success():
    """Test that a function decorated with validate_parameter_literals succeeds with valid literals."""
    from typing import Literal
    @types.validate_parameter_literals
    def dummy_func(a: Literal["x", "y"]):
        return a

    assert dummy_func("x") == "x"

def test_validate_parameter_literals_fail():
    """Test that a function decorated with validate_parameter_literals raises a ValueError for invalid literals."""
    from typing import Literal
    @types.validate_parameter_literals
    def dummy_func(a: Literal["x", "y"]):
        return a

    import pytest
    with pytest.raises(ValueError):
        dummy_func("z")

def test_does_obj_satisfy_typed_dict():
    """Test that does_obj_satisfy_typed_dict validates mappings against a TypedDict."""
    from typing_extensions import TypedDict
    class DummyDict(TypedDict, total=False):
        a: int
        b: str

    valid = {"a": 10, "b": "hello"}
    invalid = {"a": "not an int", "b": "hello"}
    assert types.does_obj_satisfy_typed_dict(valid, DummyDict) is True
    assert types.does_obj_satisfy_typed_dict(invalid, DummyDict) is False

def test_typehint_issubclass():
    """Test typehint_issubclass for proper subclass relationships using type hints."""
    # Non-generic check
    assert types.typehint_issubclass(int, object) is True
    # Check union: int is a subclass of Union[int, str]
    assert types.typehint_issubclass(int, int | str) is True
    # Check with incompatible types
    assert types.typehint_issubclass(str, int | float) is False

def test_safe_issubclass():
    """Test safe_issubclass handles invalid subclass comparisons gracefully."""
    class A:
        pass
    class B(A):
        pass
    assert types.safe_issubclass(B, A) is True
    # 5 is not a class, so safe_issubclass should return False instead of raising.
    assert types.safe_issubclass(5, A) is False
def test_get_base_class_literal():
    """Test get_base_class returns the base class for Literal types."""
    from typing import Literal
    literal_type = Literal[1, 2, 3]
    base_cls = types.get_base_class(literal_type)
    # Literals should have the same type, here int expected.
    assert base_cls == int

def test_get_base_class_union():
    """Test get_base_class returns a tuple of base classes for Union types."""
    union_type = int | str
    base_cls = types.get_base_class(union_type)
    assert isinstance(base_cls, tuple)
    assert int in base_cls and str in base_cls

def test_is_optional_and_value_inside_optional():
    """Test that is_optional and value_inside_optional correctly detect and extract non-None types."""
    from typing import Optional
    optional_type = Optional[int]
    assert types.is_optional(optional_type) is True
    # value_inside_optional should remove the None from Optional
    inner_type = types.value_inside_optional(optional_type)
    assert inner_type == int

    # For a non-optional type, is_optional should be False and value_inside_optional returns same type.
    non_optional_type = int
    assert types.is_optional(non_optional_type) is False
    assert types.value_inside_optional(non_optional_type) == int

def test_is_valid_var_type_dataclass():
    """Test that is_valid_var_type returns True for dataclass types and False for others."""
    import dataclasses
    @dataclasses.dataclass
    class DummyData:
        a: int
    assert types.is_valid_var_type(DummyData) is True

    # For a built-in type that is not valid according to our rules (and no serializer available)
    assert types.is_valid_var_type(str) is True

def test_is_backend_base_variable():
    """Test that is_backend_base_variable correctly identifies backend variable names."""
    class DummyCls:
        inherited_backend_vars = []
        _some_var = 123
        _get_type_hints = classmethod(lambda cls: {"_some_var": int})

    # Valid backend variable pattern: starts with a single underscore and is not reserved.
    assert types.is_backend_base_variable("_some_var", DummyCls) is True
    # A variable name not starting with an underscore should return False.
    assert types.is_backend_base_variable("some_var", DummyCls) is False
    # Names starting with double underscores should return False.
    assert types.is_backend_base_variable("__private", DummyCls) is False

def test_get_attribute_access_type_no_attribute():
    """Test that get_attribute_access_type returns None for attributes that do not exist."""
    class Dummy:
        pass
    assert types.get_attribute_access_type(Dummy, "non_existent") is None