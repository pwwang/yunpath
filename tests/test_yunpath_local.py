import os
import sys
import pytest
from yunpath import YPath
from pathlib import Path


def test_local_path(tmp_path):
    path = YPath(tmp_path)
    assert not path.is_cloud
    assert path.is_local
    assert path.is_dir()
    assert path.exists()
    assert str(path.resolve()) == str(tmp_path.resolve())


def test_is_mount(tmp_path):
    path = YPath("/")
    assert path.is_mount()
    path = YPath(tmp_path)
    assert not path.is_mount()


def test_is_symlink(tmp_path):
    # Create a symlink for testing
    symlink_path = tmp_path / "test_symlink"
    if os.path.exists(symlink_path):
        os.remove(symlink_path)
    os.symlink(tmp_path, symlink_path)
    path = YPath(symlink_path)
    assert path.is_symlink()
    os.remove(symlink_path)
    path = YPath(tmp_path)
    assert not path.is_symlink()


def test_stat(tmp_path):
    path = YPath(tmp_path)
    test_file = path / "test_file"
    test_file.touch()
    assert test_file.stat() is not None


def test_chmod(tmp_path):
    path = YPath(tmp_path) / "test_file"
    path.touch()
    path.chmod(0o777)
    assert oct(path.stat().st_mode)[-3:] == "777"


def test_lchmod(tmp_path):
    path = YPath(tmp_path) / "test_file"
    path.touch()
    path.lchmod(0o777)
    assert oct(path.stat().st_mode)[-3:] == "777"


def test_expanduser():
    path = YPath("~")
    assert str(path.expanduser()) == os.path.expanduser("~")


def test_group(tmp_path):
    path = YPath(tmp_path)
    assert path.group() is not None


def test_is_block_device(tmp_path):
    path = YPath(tmp_path)
    assert not path.is_block_device()


def test_is_char_device(tmp_path):
    path = YPath(tmp_path)
    assert not path.is_char_device()


def test_samefile(tmp_path):
    path1 = YPath(tmp_path)
    path2 = YPath(tmp_path)
    assert path1.samefile(path2)


def test_owner(tmp_path):
    path = YPath(tmp_path)
    assert path.owner() is not None


def test_readlink(tmp_path):
    # Create a symlink for testing
    symlink_path = tmp_path / "test_symlink"
    if os.path.exists(symlink_path):
        os.remove(symlink_path)
    os.symlink(tmp_path, symlink_path)
    path = YPath(symlink_path)
    assert path.readlink() == YPath(str(tmp_path))
    os.remove(symlink_path)
    path = YPath(tmp_path)
    with pytest.raises(OSError):
        path.readlink()


def test_rmdir(tmp_path):
    # Create a directory for testing
    test_dir = tmp_path / "test_dir"
    if not os.path.exists(test_dir):
        os.mkdir(test_dir)
    path = YPath(test_dir)
    path.rmdir()
    assert not os.path.exists(test_dir)


def test_rmtree(tmp_path):
    # Create a directory for testing
    test_dir = YPath(tmp_path) / "test_dir"
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "test_file"
    test_file.touch()
    test_dir.rmtree()
    assert not test_dir.exists()


def test_lstat(tmp_path):
    # Create a symlink for testing
    symlink_path = tmp_path / "test_symlink"
    if os.path.exists(symlink_path):
        os.remove(symlink_path)
    os.symlink(tmp_path, symlink_path)
    path = YPath(symlink_path)
    assert path.lstat() is not None
    os.remove(symlink_path)
    path = YPath(tmp_path)
    assert path.lstat() is not None


def test_symlink_to(tmp_path):
    path = YPath(tmp_path)
    with pytest.raises(OSError):
        path.symlink_to("test_symlink")


def test_touch(tmp_path):
    path = YPath(tmp_path) / "test_file"
    path.touch()
    assert path.exists()


def test_unlink(tmp_path):
    path = YPath(tmp_path) / "test_file"
    path.touch()
    assert path.exists()
    path.unlink()
    assert not path.exists()


def test_write_bytes(tmp_path):
    path = YPath(tmp_path) / "test_file"
    path.write_bytes(b"test")
    assert path.read_bytes() == b"test"


def test_write_text(tmp_path):
    path = YPath(tmp_path) / "test_file"
    path.write_text("test")
    assert path.read_text() == "test"


def test_rename(tmp_path):
    path = YPath(tmp_path) / "test_file"
    path.touch()
    path2 = path.rename(YPath(tmp_path) / "test_file2")
    assert path2.name == "test_file2"
    assert isinstance(path2, YPath)


def test_replace(tmp_path):
    path = YPath(tmp_path) / "test_file"
    path2 = YPath(tmp_path) / "test_file2"
    path2.write_text("test2")
    path.touch()
    path2 = path.replace(path2)
    assert path2.name == "test_file2"
    assert path2.read_text() == ""
    assert isinstance(path2, YPath)


def test_resolve(tmp_path):
    path = YPath(tmp_path)
    resolved_path = path.resolve()
    assert isinstance(resolved_path, YPath)
    assert resolved_path == YPath(str(tmp_path.resolve()))


def test_same_path(tmp_path):
    path1 = YPath(tmp_path)
    path2 = YPath(tmp_path)
    assert path1 == path2


def test_different_path(tmp_path):
    path1 = YPath(tmp_path)
    path2 = YPath(tmp_path / "test")
    assert path1 != path2


def test_hash(tmp_path):
    path1 = YPath(tmp_path)
    path2 = YPath(tmp_path)
    assert hash(path1) == hash(path2)


def test_repr(tmp_path):
    path = YPath(tmp_path)
    assert repr(path) == f"YPath('{tmp_path}')"


def test_joinpath(tmp_path):
    path = YPath(tmp_path)
    new_path = path.joinpath("test")
    assert isinstance(new_path, YPath)
    assert new_path == YPath(tmp_path) / "test"


def test_rtruediv(tmp_path):
    path = YPath("test")
    new_path = str(tmp_path) / path
    assert isinstance(new_path, YPath)
    assert new_path == YPath(tmp_path) / "test"


def test_cwd():
    path = YPath.cwd()
    assert isinstance(path, YPath)
    assert path.resolve() == YPath(os.getcwd()).resolve()

    path = YPath()
    assert isinstance(path, YPath)
    assert path.resolve() == YPath(os.getcwd()).resolve()


def test_home():
    path = YPath.home()
    assert isinstance(path, YPath)
    assert path == YPath(os.path.expanduser("~"))


def test_exists(tmp_path):
    path = YPath(tmp_path)
    assert path.exists()
    path = YPath(tmp_path) / "test_file_not_exists"
    assert not path.exists()


def test_glob(tmp_path):
    path = YPath(tmp_path)
    test_file1 = path / "test_file1"
    test_file2 = path / "test_file2"
    test_file1.touch()
    test_file2.touch()
    files = list(path.glob("*"))
    assert len(files) == 2
    assert all(isinstance(f, YPath) for f in files)


def test_rglob(tmp_path):
    path = YPath(tmp_path)
    test_dir = path / "test_dir"
    test_dir.mkdir()
    test_file1 = path / "test_file1"
    test_file2 = test_dir / "test_file2"
    test_file1.touch()
    test_file2.touch()
    files = list(path.rglob("*"))
    assert len(files) == 3
    assert all(isinstance(f, YPath) for f in files)


def test_is_dir(tmp_path):
    path = YPath(tmp_path)
    assert path.is_dir()

    test_file = path / "test_file"
    path = YPath(test_file)
    test_file.touch()
    assert not path.is_dir()


def test_is_file(tmp_path):
    path = YPath(tmp_path) / "test_file"
    path.touch()
    assert path.is_file()
    path.unlink()
    assert not path.is_file()


def test_is_socket(tmp_path):
    path = YPath(tmp_path)
    assert not path.is_socket()


def test_is_fifo(tmp_path):
    path = YPath(tmp_path)
    assert not path.is_fifo()


def test_iterdir(tmp_path):
    path = YPath(tmp_path)
    test_file1 = path / "test_file1"
    test_file2 = path / "test_file2"
    test_file1.touch()
    test_file2.touch()
    files = list(path.iterdir())
    assert len(files) == 2
    assert all(isinstance(f, YPath) for f in files)


def test_match(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.match("test_file")


def test_name(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.name == "test_file"


def test_parent(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert isinstance(path.parent, YPath)
    assert path.parent == YPath(tmp_path)


def test_parts(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.parts[-1] == "test_file"


def test_with_name(tmp_path):
    path = YPath(tmp_path) / "test_file"
    new_path = path.with_name("test_file2")
    assert isinstance(new_path, YPath)
    assert new_path == YPath(tmp_path) / "test_file2"


def test_with_suffix():
    path = YPath("test_file.txt")
    new_path = path.with_suffix(".csv")
    assert isinstance(new_path, YPath)
    assert new_path == YPath("test_file.csv")


def test_suffix():
    path = YPath("test_file.txt")
    assert path.suffix == ".txt"


def test_suffixes():
    path = YPath("test_file.tar.gz")
    assert path.suffixes == [".tar", ".gz"]


def test_stem():
    path = YPath("test_file.txt")
    assert path.stem == "test_file"


def test_as_posix(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.as_posix() == str(path)


def test_as_uri(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.as_uri().startswith("file://")


def test_drive(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.drive == ""


def test_root(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.root == "/"


def test_anchor(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.anchor == "/"


def test_relative_to(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.relative_to(tmp_path) == YPath("test_file")


def test_is_absolute(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.is_absolute() is True

    path = YPath("test_file")
    assert path.absolute() == YPath.cwd().joinpath("test_file").absolute()


def test_is_reserved(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.is_reserved() is False


def test_joinpath_multiple(tmp_path):
    path = YPath(tmp_path)
    new_path = path.joinpath("dir1", "dir2", "file")
    assert isinstance(new_path, YPath)
    assert new_path == YPath(tmp_path) / "dir1" / "dir2" / "file"


def test_with_stem(tmp_path):
    path = YPath(tmp_path) / "test_file.txt"
    new_path = path.with_stem("new_stem")
    assert isinstance(new_path, YPath)
    assert new_path == YPath(tmp_path) / "new_stem.txt"


def test_open(tmp_path):
    path = YPath(tmp_path) / "test_file"
    with path.open("w") as f:
        f.write("test")
    with path.open("r") as f:
        assert f.read() == "test"


def test_walk(tmp_path):
    path = YPath(tmp_path)
    test_dir = path / "test_dir"
    test_dir.mkdir()
    test_file1 = test_dir / "test_file1"
    test_file2 = test_dir / "test_file2"
    test_file1.touch()
    test_file2.touch()
    for root, dirs, files in path.walk():
        assert isinstance(root, YPath)
        assert all(isinstance(d, str) for d in dirs)
        assert all(isinstance(f, str) for f in files)


def test_hardlink_to(tmp_path):
    path = YPath(tmp_path) / "test_file"
    path.touch()
    link_path = YPath(tmp_path) / "test_file_link"
    link_path.hardlink_to(path)
    assert link_path.exists()
    assert link_path.samefile(path)


def test_from_uri(tmp_path):
    path = YPath(tmp_path) / "test_file"
    uri = path.as_uri()
    new_path = YPath.from_uri(uri)
    assert isinstance(new_path, YPath)
    assert new_path == path

    with pytest.raises(ValueError):
        YPath.from_uri("file:a/b")

    with pytest.raises(ValueError):
        YPath.from_uri("xyz://a/b")


def test_full_match(tmp_path):
    path = YPath(tmp_path) / "test_file"

    if sys.version_info < (3, 13):
        with pytest.raises(NotImplementedError):
            path.full_match("test_file")
    else:
        assert not path.full_match("test_file")
        assert path.full_match(str(tmp_path) + "/test_*")


def test_is_relative_to(tmp_path):
    path = YPath(tmp_path) / "test_file"
    assert path.is_relative_to(tmp_path)


def test_parents(tmp_path):
    path = YPath(tmp_path) / "test_file"
    parents = path.parents
    assert all(isinstance(p, YPath) for p in parents)


# Comparing yunpath.YPath with pathlib.YPath
def test_local_path_comparison(tmp_path):
    ypath = YPath(tmp_path)
    ppath = Path(tmp_path)
    assert ypath == ppath
    assert isinstance(ypath, YPath)
    assert isinstance(ppath, Path)


def test_same_behavior_local(tmp_path):
    ypath = YPath(tmp_path) / "test1.txt"
    ppath = Path(tmp_path) / "test2.txt"

    ypath.write_text("yunpath")
    ppath.write_text("pathlib")

    assert ypath.read_text() == "yunpath"
    assert ppath.read_text() == "pathlib"

    assert ypath.exists() == ppath.exists()
    assert ypath.is_file() == ppath.is_file()

    ypath.unlink()
    ppath.unlink()

    assert not ypath.exists()
    assert not ppath.exists()


def test_yunpath_pathlib_interchangeability(tmp_path):
    # Create a file using yunpath
    ypath = YPath(tmp_path) / "test_file_ypath.txt"
    ypath.write_text("Written by yunpath")

    # Create a YPathlib path from the yunpath path
    ppath = Path(str(ypath))

    # Assert that the file exists and can be read by YPathlib
    assert ppath.exists()
    assert ppath.read_text() == "Written by yunpath"

    # Clean up
    ypath.unlink()
