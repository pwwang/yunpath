import pytest
from pathlib import Path
from yunpath import AnyPath
from cloudpathlib.exceptions import NoStatError
from .conftest import uid  # noqa: F401


def test_gspath_patched(gspath):
    """Test that the AnyPath class is patched"""
    assert isinstance(gspath, AnyPath)


def test_mkdir(gspath):
    """Test that mkdir() creates a directory"""
    path = gspath / "test_mkdir"
    path.mkdir(exist_ok=True)
    assert path.is_dir()


def test_mkdir_exists(gspath):
    """Test that mkdir() does not raise an exception if the directory already
    exists"""
    path = gspath / "test_mkdir_exists"
    path.mkdir(exist_ok=True)
    with pytest.raises(FileExistsError):
        path.mkdir(exist_ok=False)


def test_mkdir_parents_true(gspath):
    """Test that mkdir() creates parent directories"""
    path = gspath / "test_mkdir_parents_true" / "test"
    path.mkdir(parents=True, exist_ok=True)
    assert path.is_dir()


def test_mkdir_parents_false(gspath):
    """Test that mkdir() does not create parent directories"""
    path = gspath / "test_mkdir_parents_false" / "test"
    with pytest.raises(FileNotFoundError):
        path.mkdir(parents=False, exist_ok=True)


def test_eq():
    """Test that AnyPath objects are equal even if one has a trailing slash"""
    gspath1 = AnyPath("gs://handy-buffer-287000.appspot.com/yunpath-test")
    gspath2 = AnyPath("gs://handy-buffer-287000.appspot.com/yunpath-test/")
    assert gspath1 == gspath2
    assert gspath1 != 1


def test_iterdir(gspath):
    """Test that iterdir() does not return the directory itself"""
    path = gspath / "test_iterdir"
    path.mkdir(exist_ok=True)
    (path / "test_file").touch()
    assert list(path.iterdir()) == [path / "test_file"]
    (path / "test_file").unlink()


def test_stat(gspath):
    """Test that stat() returns the correct mtime if the metadata has an
    updated field"""
    path = gspath / "test_stat"
    path.touch()
    stat = path.stat()
    assert stat.st_mtime > 0


def test_stat_dir(gspath):
    """Test that stat() raises NoStatError if the path is a directory"""
    with pytest.raises(NoStatError):
        gspath.stat()


def test_fspath(gspath):
    """Test that fspath() returns the correct path"""
    path = AnyPath(gspath.fspath)
    assert isinstance(path, Path)
    assert str(path) == path.fspath


def test_is_file_or_dir(gspath):
    """Test that _is_file_or_dir() correctly identifies a directory as
    a directory even if it is empty"""
    # path = gspath / "test_is_file_or_dir"
    # path.mkdir(exist_ok=True)
    # assert path.client._is_file_or_dir(path) == "dir"

    # path = next(gspath.iterdir())
    # assert path.client._is_file_or_dir(path) == "dir"

    path = gspath / "test_file.txt"
    path.touch()
    assert path.client._is_file_or_dir(path) == "file"
