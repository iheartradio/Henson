"""Test importer."""

import pytest

from ingestion.importer import import_from_service, ServiceImportError


def test_import_from_service(mock_service):
    """Test import_from_service."""
    settings = import_from_service('mock_service', 'settings')
    assert hasattr(settings, 'SERVICE_SETTING')


def test_import_from_service_propagates_exceptions(mock_service):
    """Test import_from_service propagates exceptions."""
    with pytest.raises(TypeError) as e:
        import_from_service('mock_service', 'type_error')


def test_import_from_service_propagates_importerror(mock_service):
    """Test import_from_service propagates ImportError."""
    with pytest.raises(ImportError) as e:
        import_from_service('mock_service', 'bad_import')
    assert not isinstance(e, ServiceImportError)


def test_import_from_service_no_module_raises_serviceimporterror(mock_service):
    """Test import_from_service when requested module doesn't exist."""
    with pytest.raises(ServiceImportError):
        import_from_service('mock_service', 'not_a_real_module')


def test_import_from_service_no_service_raises_serviceimporterror():
    """Test import_from_service when requested service doesn't exist."""
    with pytest.raises(ServiceImportError):
        import_from_service('not_a_real_service', 'no_module')
