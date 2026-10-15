import importlib
from importlib import metadata


def test_project_package_is_importable() -> None:
    jev_as_jungle_engine = importlib.import_module("jev_as_jungle_engine")

    assert jev_as_jungle_engine.__version__ == metadata.version("jev-as-jungle-engine")
