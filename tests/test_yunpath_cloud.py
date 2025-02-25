import sys
import pytest
from yunpath import AnyPath
from .conftest import uid  # noqa: F401


@pytest.fixture(scope="module")
def gspath(uid):  # noqa: F811
    """Return a GSYPath object"""
    p = AnyPath(
        f"gs://handy-buffer-287000.appspot.com/yunpath-test/test-{uid}"
    )
    p.mkdir(exist_ok=True)
    yield p
    p.rmtree()


def test_cloud_path(gspath):
    path = gspath
    assert path.is_cloud
    assert not path.is_local
    assert path.is_dir()
    assert path.exists()
    assert path.bucket == "handy-buffer-287000.appspot.com"
    assert str(path.resolve()).startswith("gs://")


def test_stat(gspath):
    path = gspath / "test_stat"
    path.touch()
    assert path.stat() is not None


def test_chmod(gspath):
    path = gspath
    with pytest.raises(NotImplementedError):
        path.chmod(0o777)


def test_lchmod(gspath):
    path = gspath
    with pytest.raises(NotImplementedError):
        path.lchmod(0o777)


def test_expanduser(gspath):
    with pytest.raises(NotImplementedError):
        gspath.expanduser()


def test_group(gspath):
    path = gspath
    with pytest.raises(NotImplementedError):
        path.group()


def test_is_block_device(gspath):
    assert gspath.is_block_device() is False


def test_is_char_device(gspath):
    assert gspath.is_char_device() is False


def test_samefile(gspath):
    path1 = gspath
    path2 = gspath
    assert path1.samefile(path2)


def test_owner(gspath):
    path = gspath
    with pytest.raises(NotImplementedError):
        path.owner()


def test_readlink(gspath):
    path = gspath
    with pytest.raises(NotImplementedError):
        path.readlink()


def test_rmdir(gspath):
    path = gspath.joinpath("test_dir")
    path.rmdir()


def test_lstat(gspath):
    with pytest.raises(NotImplementedError):
        gspath.lstat()


def test_symlink_to(gspath):
    path = gspath
    with pytest.raises(NotImplementedError):
        path.symlink_to("test_symlink")


def test_touch(gspath):
    path = gspath.joinpath("test_file")
    path.touch()
    assert path.exists()


def test_unlink(gspath):
    path = gspath.joinpath("test_file")
    path.touch()
    assert path.exists()
    path.unlink()
    assert not path.exists()


def test_write_bytes(gspath):
    path = gspath.joinpath("test_file")
    path.write_bytes(b"test")
    assert path.read_bytes() == b"test"


def test_write_text(gspath):
    path = gspath.joinpath("test_file")
    path.write_text("test")
    assert path.read_text() == "test"


def test_rename(gspath):
    path = gspath.joinpath("test_file")
    path.touch()
    path2 = path.rename(gspath / "test_file2")
    assert path2.name == "test_file2"
    assert isinstance(path2, AnyPath)


def test_replace(gspath):
    path = gspath.joinpath("test_file")
    path2 = gspath.joinpath("test_file2")
    path2.write_text("test2")
    path.touch()
    path2 = path.replace(path2)
    assert path2.name == "test_file2"
    assert path2.read_text() == ""
    assert isinstance(path2, AnyPath)


def test_resolve(gspath):
    path = gspath
    assert str(path.resolve()).startswith("gs://")


def test_same_path(gspath):
    path1 = gspath
    path2 = gspath
    assert path1 == path2


def test_different_path(gspath):
    path1 = gspath
    path2 = AnyPath("gs://handy-buffer-287000.appspot.com/yunpath-test2")
    assert path1 != path2


def test_hash(gspath):
    path1 = gspath
    path2 = gspath
    assert hash(path1) == hash(path2)


def test_repr(gspath):
    path = gspath
    print(repr(path))
    assert repr(path).startswith(
        "AnyPath('gs://handy-buffer-287000.appspot.com/yunpath-test/"
    )


def test_joinpath(gspath):
    path = gspath
    new_path = path.joinpath("test")
    assert new_path == gspath / "test"


def test_rtruediv(gspath):
    new_path = gspath / "test"
    assert new_path.name == "test"


def test_exists(gspath):
    path = gspath
    assert path.exists()


def test_glob(gspath):
    path = gspath / "test_glob"
    path.mkdir(exist_ok=True)
    (path / "test1.txt").touch()
    (path / "test2.txt").touch()
    (path / "test3.txt").touch()
    assert len(list(path.glob("*.txt"))) == 3


def test_rglob(gspath):
    path = gspath / "test_rglob"
    path.mkdir(exist_ok=True)
    subpath = path / "subdir"
    subpath.mkdir(exist_ok=True)
    (path / "test1.txt").touch()
    (path / "test2.txt").touch()
    (subpath / "test3.txt").touch()
    assert len(list(path.rglob("*.txt"))) == 3


def test_is_dir(gspath):
    path = gspath
    assert path.is_dir()

    path = path / "test_file"
    assert not path.is_dir()

    path.touch()
    assert not path.is_dir()


def test_is_file(gspath):
    path = gspath.joinpath("not_a_file_yet")
    assert not path.is_file()
    path.touch()
    assert path.is_file()


def test_is_socket(gspath):
    path = gspath
    assert not path.is_socket()


def test_is_fifo(gspath):
    path = gspath
    assert not path.is_fifo()


def test_iterdir(gspath):
    path = gspath / "test_iterdir"
    path.mkdir(exist_ok=True)
    (path / "test1.txt").touch()
    (path / "test2.txt").touch()
    for p in path.iterdir():
        assert isinstance(p, AnyPath)


def test_match(gspath):
    path = gspath
    assert path.match("gs://handy-buffer-287000.appspot.com/yunpath-test/*")
    path = gspath / "test_file"
    path.match("test_file")


def test_name(gspath):
    path = gspath
    assert path.parent.name == "yunpath-test"


def test_parent(gspath):
    path = gspath / "test_file"
    assert path.parent == gspath


def test_parts(gspath):
    path = gspath
    assert len(path.parts) == 4
    assert path.parts[:3] == (
        "gs://",
        "handy-buffer-287000.appspot.com",
        "yunpath-test",
    )


def test_with_name(gspath):
    path = gspath
    new_path = path.with_name("test_file2")
    assert new_path.name == "test_file2"


def test_with_suffix(gspath):
    path = gspath.joinpath("yunpath-test.txt")
    new_path = path.with_suffix(".csv")
    assert new_path.name == "yunpath-test.csv"


def test_suffix(gspath):
    path = gspath.joinpath("yunpath-test.txt")
    assert path.suffix == ".txt"


def test_suffixes(gspath):
    path = gspath.joinpath("yunpath-test.tar.gz")
    assert path.suffixes == [".tar", ".gz"]


def test_stem(gspath):
    path = gspath.joinpath("yunpath-test.txt")
    assert path.stem == "yunpath-test"


def test_as_posix(gspath):
    path = gspath / "test_file"
    assert path.as_posix() == str(path)


def test_as_uri(gspath):
    path = gspath / "test_file"
    assert path.as_uri().startswith("gs://")


def test_drive(gspath):
    path = gspath / "test_file"
    assert path.drive == "handy-buffer-287000.appspot.com"


def test_root(gspath):
    with pytest.raises(NotImplementedError):
        gspath.root


def test_anchor(gspath):
    path = gspath / "test_file"
    assert path.anchor == "gs://"


def test_relative_to(gspath):
    path = gspath / "test_file"
    assert path.relative_to(gspath) == AnyPath("test_file")


def test_is_absolute(gspath):
    path = gspath / "test_file"
    assert path.is_absolute() is True
    assert path.absolute() == path


def test_is_reserved(gspath):
    path = gspath / "test_file"
    assert path.is_reserved() is False


def test_joinpath_multiple(gspath):
    path = gspath
    new_path = path.joinpath("dir1", "dir2", "file")
    assert isinstance(new_path, AnyPath)
    assert new_path == gspath / "dir1" / "dir2" / "file"


def test_with_stem(gspath):
    path = gspath / "yunpath-test.txt"
    new_path = path.with_stem("new_stem")
    assert new_path == gspath / "new_stem.txt"


def test_open(gspath):
    path = gspath / "test_file"
    with path.open("w") as f:
        f.write("test")
    with path.open("r") as f:
        assert f.read() == "test"


def test_walk(gspath):
    path = gspath / "test_dir"
    path.mkdir(exist_ok=True)
    (path / "test_file1").touch()
    (path / "test_file2").touch()
    for root, dirs, files in path.walk():
        assert isinstance(root, AnyPath)
        assert all(isinstance(d, str) for d in dirs)
        assert all(isinstance(f, str) for f in files)


def test_hardlink_to(gspath):
    path = gspath / "test_file"
    with pytest.raises(NotImplementedError):
        path.hardlink_to(gspath / "test_file_link")


def test_from_uri(gspath):
    path = gspath / "test_file"
    uri = path.as_uri()
    new_path = AnyPath.from_uri(uri)
    assert isinstance(new_path, AnyPath)
    assert new_path == path


def test_full_match(gspath):
    path = gspath / "test_file"
    if sys.version_info < (3, 13):
        with pytest.raises(NotImplementedError):
            path.full_match("test_file")
    else:
        assert not path.full_match("test_file")
        assert path.full_match("gs://handy-buffer-287000.appspot.com/yunpath-test/*/*")


def test_is_relative_to(gspath):
    path = gspath / "test_file"
    assert path.is_relative_to(gspath)


def test_parents(gspath):
    path = gspath / "test_file"
    parents = path.parents
    assert all(isinstance(p, AnyPath) for p in parents)


# Comparing yunpath.AnyPath with pathlib.AnyPath
def test_cloud_path_comparison(gspath):
    ypath = gspath
    ppath = AnyPath(str(gspath))
    assert ypath == ppath
    assert isinstance(ypath, AnyPath)
    assert isinstance(ppath, AnyPath)
