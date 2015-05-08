"""Test the application registry."""


def test_adding_to_empty_registry(registry):
    """Test that adding to an empty registry returns the added app."""
    obj = object()
    registry.current_application = obj
    assert registry.current_application == obj


def test_adding_multiple_to_registry(registry):
    """Test that a registry returns the newest app added."""
    obj1 = object()
    obj2 = object()
    registry.current_application = obj1
    registry.current_application = obj2
    assert registry.current_application == obj2


def test_empty_registry(registry):
    """Test that an empty registry returns None."""
    assert registry.current_application is None


def test_registry_retains_apps(registry):
    """Test that a registry retains all previous apps."""
    obj1 = object()
    obj2 = object()
    registry.current_application = obj1
    registry.current_application = obj2
    # This is an implementation detail and probably needs to be tested
    # in a better way.
    assert obj1 in registry._applications
