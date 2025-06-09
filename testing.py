from typing import NewType
import pathlib
import pytest


def has_test_dir(mod_path: pathlib.Path) -> bool:
    test_dir = mod_path / '.test'
    return test_dir.exists() and test_dir.is_dir()


def test(mod_path: pathlib.Path) -> bool:
    test_dir = mod_path / '.test'
    assert has_test_dir(mod_path), f"!!! No test dir found: {test_dir}"
    print(f'running pytest {str(test_dir)}')

    return pytest.main([str(test_dir)]) == 0
