"""Test the configuration utility."""

from verona.config import Config


def test_config_from_mapping():
    """Test Config.from_mapping."""
    config = Config()
    config.from_mapping({'A': 1})
    assert config['A'] == 1


def test_config_from_mapping_overwrites():
    """Test that Config.from_mapping overwrites existing keys."""
    config = Config(B=1)
    config.from_mapping({'B': 2})
    assert config['B'] == 2


def test_config_from_object(settings):
    """Test Config.from_object."""
    config = Config()
    config.from_object(settings)
    assert config['A'] == 1


def test_config_from_object_overwrites(settings):
    """Test that Config.from_object overwrites existing keys."""
    config = Config(B=1)
    config.from_object(settings)
    assert config['B'] == 2
