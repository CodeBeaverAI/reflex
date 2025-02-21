import json
import os
import pytest
from reflex.base import (
    Base,
    pydantic_main,
    validate_field_name,
)
from reflex.utils.exceptions import (
    VarNameError,
)


@pytest.fixture
def child() -> Base:
    """A child class.

    Returns:
        A child class.
    """

    class Child(Base):
        num: float
        key: str

    return Child(num=3.14, key="pi")


def test_get_fields(child):
    """Test that the fields are set correctly.

    Args:
        child: A child class.
    """
    assert child.get_fields().keys() == {"num", "key"}


def test_set(child):
    """Test setting fields.

    Args:
        child: A child class.
    """
    child.set(num=1, key="a")
    assert child.num == 1
    assert child.key == "a"


def test_json(child):
    """Test converting to json.

    Args:
        child: A child class.
    """
    assert child.json().replace(" ", "") == '{"num":3.14,"key":"pi"}'


@pytest.fixture
def complex_child() -> Base:
    """A child class.

    Returns:
        A child class.
    """

    class Child(Base):
        num: float
        key: str
        name: str
        age: int
        active: bool

    return Child(num=3.14, key="pi", name="John Doe", age=30, active=True)


def test_complex_get_fields(complex_child):
    """Test that the fields are set correctly.

    Args:
        complex_child: A child class.
    """
    assert complex_child.get_fields().keys() == {"num", "key", "name", "age", "active"}


def test_complex_set(complex_child):
    """Test setting fields.

    Args:
        complex_child: A child class.
    """
    complex_child.set(num=1, key="a", name="Jane Doe", age=28, active=False)
    assert complex_child.num == 1
    assert complex_child.key == "a"
    assert complex_child.name == "Jane Doe"
    assert complex_child.age == 28
    assert complex_child.active is False


def test_complex_json(complex_child):
    """Test converting to json.

    Args:
        complex_child: A child class.
    """
    assert (
        complex_child.json().replace(" ", "")
        == '{"num":3.14,"key":"pi","name":"JohnDoe","age":30,"active":true}'
    )


def test_add_field_and_get_value():
    """
    Test adding a field dynamically using add_field and retrieving field values
    using get_value. This ensures that dynamic field addition works and that
    get_value returns the actual attribute value if it exists or the key if it does not.
    """

    class DummyVar:
        _var_field_name = "dummy"
        _var_type = int

    class Child(Base):
        existing: str

    child = Child(existing="value")
    assert "dummy" not in Child.get_fields()
    Child.add_field(DummyVar(), 42)
    assert "dummy" in Child.get_fields()
    assert child.get_value("existing") == "value"
    assert child.get_value("nonexistent") == "nonexistent"


def test_validate_field_name_no_error():
    """
    Test that validate_field_name does not raise an error when attribute access works normally.
    This simulates a scenario where the base does not have the specified field.
    """

    class Dummy:
        pass

    os.environ["__RELOAD_CONFIG"] = "false"
    validate_field_name([Dummy], "test_field")


def test_validate_field_name_error():
    """
    Test that validate_field_name raises a VarNameError when a TypeError occurs during attribute access.
    This is done by creating a dummy base class that raises a TypeError when a certain attribute is accessed.
    """
    os.environ["__RELOAD_CONFIG"] = "false"

    class BadBase:

        def __getattribute__(self, name):
            if name == "bad_field":
                raise TypeError("Intentional error for testing")
            return super().__getattribute__(name)

    with pytest.raises(VarNameError) as excinfo:
        validate_field_name([BadBase()], "bad_field")
    assert 'State var "bad_field"' in str(excinfo.value)


def test_get_value_non_string():
    """
    Test that get_value returns the key unchanged when a non-string key is provided.
    This covers the branch in get_value where the key is not a string.
    """

    class Child(Base):
        dummy: int

    instance = Child(dummy=100)
    non_string_key = (1, 2, 3)
    assert instance.get_value(non_string_key) == non_string_key


def test_validate_field_name_reload_true():
    """
    Test that validate_field_name does NOT raise a VarNameError when
    the __RELOAD_CONFIG environment variable is set to "true", even if
    a base class would raise a TypeError on attribute access.
    """
    os.environ["__RELOAD_CONFIG"] = "true"

    class BadBase:

        def __getattribute__(self, name):
            if name == "test_field":
                raise TypeError("Intentional TypeError for testing reload behavior")
            return super().__getattribute__(name)

    try:
        validate_field_name([BadBase()], "test_field")
    except VarNameError as e:
        pytest.fail(
            f"validate_field_name raised VarNameError when __RELOAD_CONFIG is true: {e}"
        )
    finally:
        os.environ["__RELOAD_CONFIG"] = "false"


def test_extra_field_serialized():
    """
    Test that setting an extra field using set() attaches the extra field to the instance,
    is not registered in the declared fields (via get_fields()), but is included in the outputs of
    dict() and json() serialization. This reflects the actual behavior when extra fields are added
    via setattr().
    """

    class Child(Base):
        existing: str

    child = Child(existing="value")
    returned = child.set(extra="ignored")
    assert returned is child
    assert getattr(child, "extra") == "ignored"
    assert "extra" not in child.get_fields()
    data = child.dict()
    expected_data = {"existing": "value", "extra": "ignored"}
    assert data == expected_data
    json_output = child.json()
    parsed = json.loads(json_output)
    assert parsed == expected_data


def test_get_fields_on_base():
    """
    Test that Base.get_fields() returns an empty dictionary when no fields are declared
    on the Base class itself.
    """
    fields = Base.get_fields()
    assert fields == {}, f"Expected an empty dict but got: {fields}"


def test_custom_serialize_in_json(monkeypatch):
    """
    Test that Base.json uses custom serialization via its default serialize function.
    This test monkeypatches the 'reflex.utils.serializers.serialize' function so that
    a custom Dummy type is serialized to a recognizable string.
    """

    class Dummy:

        def __init__(self, value):
            self.value = value

    def dummy_serialize(obj):
        if isinstance(obj, Dummy):
            return f"dummy_serialized_{obj.value}"
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    monkeypatch.setattr("reflex.utils.serializers.serialize", dummy_serialize)

    class Child(Base):
        dummy: Dummy

    dummy_instance = Dummy("example")
    child = Child(dummy=dummy_instance)
    json_output = child.json()
    parsed = json.loads(json_output)
    assert parsed["dummy"] == "dummy_serialized_example"


def test_pydantic_validate_field_name_monkeypatched():
    """
    Test that pydantic_main.validate_field_name has been monkeypatched to use our
    custom validate_field_name function. This ensures that the monkeypatch behavior in
    reflex/base.py is correctly applied.
    """
    assert pydantic_main.validate_field_name is validate_field_name


def test_custom_json_dumps(monkeypatch):
    """
    Test that Base.json uses a custom json_dumps function from the __config__.
    We monkeypatch __config__.json_dumps to return a specific string and verify that
    json() returns that string.
    """

    class Child(Base):
        field: int

    child = Child(field=10)
    monkeypatch.setattr(
        child.__config__, "json_dumps", lambda obj, default=None: "custom-dump"
    )
    assert child.json() == "custom-dump"
