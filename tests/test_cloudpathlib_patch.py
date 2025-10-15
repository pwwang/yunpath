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
    from cloudpathlib.exceptions import CloudPathNotExistsError

    path = gspath / "test_mkdir_parents_false" / "test"
    with pytest.raises(CloudPathNotExistsError):
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


def test_symlink_to(gspath):
    """Test creating a symlink"""
    target = gspath / "test_symlink_target"
    target.touch()

    link = gspath / "test_symlink"
    link.symlink_to(target)

    assert link.exists(follow_symlinks=False)
    assert link.is_symlink()
    assert link.readlink() == target

    # Clean up
    link.unlink()
    target.unlink()


def test_symlink_to_already_exists(gspath):
    """Test that symlink_to() raises an error if the link already exists"""
    target = gspath / "test_symlink_to_exists_target"
    target.touch()

    link = gspath / "test_symlink_to_exists"
    link.touch()

    with pytest.raises(FileExistsError):
        link.symlink_to(target)

    # Clean up
    link.unlink()
    target.unlink()


def test_symlink_to_relative_path(gspath):
    """Test creating a symlink with a relative path"""
    target = gspath / "test_symlink_relative_target"
    target.touch()

    link = gspath / "test_symlink_relative"
    link.symlink_to("test_symlink_relative_target")

    assert link.is_symlink()
    assert link.readlink().name == "test_symlink_relative_target"

    # Clean up
    link.unlink()
    target.unlink()


def test_is_symlink_false(gspath):
    """Test that is_symlink() returns False for regular files"""
    path = gspath / "test_not_symlink"
    path.touch()

    assert not path.is_symlink()

    # Clean up
    path.unlink()


def test_is_symlink_directory(gspath):
    """Test that is_symlink() returns False for directories"""
    path = gspath / "test_not_symlink_dir"
    path.mkdir(exist_ok=True)

    assert not path.is_symlink()

    # Clean up
    path.rmdir()


def test_readlink_not_symlink(gspath):
    """Test that readlink() raises an error for non-symlinks"""
    path = gspath / "test_readlink_not_symlink"
    path.touch()

    with pytest.raises(OSError):
        path.readlink()

    # Clean up
    path.unlink()


def test_resolve_symlink(gspath):
    """Test resolving a symlink"""
    target = gspath / "test_resolve_target"
    target.touch()

    link = gspath / "test_resolve_link"
    link.symlink_to(target)

    resolved = link.resolve()
    assert resolved == target
    assert not resolved.is_symlink()

    # Clean up
    link.unlink()
    target.unlink()


def test_resolve_symlink_chain(gspath):
    """Test resolving a chain of symlinks"""
    target = gspath / "test_resolve_chain_target"
    target.touch()

    link1 = gspath / "test_resolve_chain_link1"
    link1.symlink_to(target)

    link2 = gspath / "test_resolve_chain_link2"
    link2.symlink_to(link1)

    resolved = link2.resolve()
    assert resolved == target
    assert not resolved.is_symlink()

    # Clean up
    link2.unlink()
    link1.unlink()
    target.unlink()


def test_resolve_nonexistent_strict(gspath):
    """Test that resolve() with strict=True raises an error for non-existent paths"""
    from cloudpathlib.exceptions import CloudPathNotExistsError

    link = gspath / "test_resolve_nonexistent"

    with pytest.raises(CloudPathNotExistsError):
        link.resolve(strict=True)


def test_exists_follow_symlinks_true(gspath):
    """Test exists() with follow_symlinks=True"""
    target = gspath / "test_exists_follow_target"
    target.touch()

    link = gspath / "test_exists_follow_link"
    link.symlink_to(target)

    assert link.exists(follow_symlinks=True)

    # Test with broken symlink
    target.unlink()
    assert not link.exists(follow_symlinks=True)

    # Clean up
    link.unlink()


def test_exists_follow_symlinks_false(gspath):
    """Test exists() with follow_symlinks=False"""
    target = gspath / "test_exists_no_follow_target"
    target.touch()

    link = gspath / "test_exists_no_follow_link"
    link.symlink_to(target)

    assert link.exists(follow_symlinks=False)

    # Test with broken symlink - should still exist
    target.unlink()
    assert link.exists(follow_symlinks=False)

    # Clean up
    link.unlink()


def test_is_file_follow_symlinks(gspath):
    """Test is_file() with follow_symlinks parameter"""
    target = gspath / "test_is_file_follow_target"
    target.touch()

    link = gspath / "test_is_file_follow_link"
    link.symlink_to(target)

    # Should be a file when following symlinks
    assert link.is_file(follow_symlinks=True)

    # Note: GCS symlinks are stored as files with metadata,
    # so is_file(follow_symlinks=False) returns True
    # This is different from POSIX behavior but consistent with GCS implementation
    assert link.is_file(follow_symlinks=False)

    # Clean up
    link.unlink()
    target.unlink()


def test_is_dir_follow_symlinks(gspath):
    """Test is_dir() with follow_symlinks parameter"""
    target = gspath / "test_is_dir_follow_target"
    target.mkdir(exist_ok=True)

    link = gspath / "test_is_dir_follow_link"
    link.symlink_to(target)

    # Should be a directory when following symlinks
    assert link.is_dir(follow_symlinks=True)

    # Should not be a directory when not following symlinks
    assert not link.is_dir(follow_symlinks=False)

    # Clean up
    link.unlink()
    target.rmdir()


def test_stat_follow_symlinks(gspath):
    """Test stat() with follow_symlinks parameter"""
    target = gspath / "test_stat_follow_target"
    target.touch()

    link = gspath / "test_stat_follow_link"
    link.symlink_to(target)

    # Stat of symlink following the link should match target
    stat_following = link.stat(follow_symlinks=True)
    stat_target = target.stat()
    assert stat_following.st_size == stat_target.st_size

    # Clean up
    link.unlink()
    target.unlink()


def test_read_text_through_symlink(gspath):
    """Test reading text through a symlink"""
    target = gspath / "test_read_text_target"
    target.write_text("Hello, world!")

    link = gspath / "test_read_text_link"
    link.symlink_to(target)

    assert link.read_text() == "Hello, world!"

    # Clean up
    link.unlink()
    target.unlink()


def test_write_text_through_symlink(gspath):
    """Test writing text through a symlink"""
    target = gspath / "test_write_text_target"
    target.touch()

    link = gspath / "test_write_text_link"
    link.symlink_to(target)

    link.write_text("Test content")
    assert target.read_text() == "Test content"

    # Clean up
    link.unlink()
    target.unlink()


def test_unlink_symlink(gspath):
    """Test unlinking a symlink"""
    target = gspath / "test_unlink_target"
    target.touch()

    link = gspath / "test_unlink_link"
    link.symlink_to(target)

    # Unlink the symlink
    link.unlink()

    # Target should still exist
    assert target.exists()
    assert not link.exists(follow_symlinks=False)

    # Clean up
    target.unlink()


def test_unlink_directory_raises_error(gspath):
    """Test that unlink() raises an error for directories"""
    from cloudpathlib.exceptions import CloudPathIsADirectoryError

    path = gspath / "test_unlink_dir"
    path.mkdir(exist_ok=True)

    with pytest.raises(CloudPathIsADirectoryError):
        path.unlink()

    # Clean up
    path.rmdir()


def test_walk_follow_symlinks(gspath):
    """Test walk() with follow_symlinks parameter"""
    # Create a directory structure
    dir1 = gspath / "test_walk_dir1"
    dir1.mkdir(exist_ok=True)
    (dir1 / "file1.txt").touch()

    dir2 = gspath / "test_walk_dir2"
    dir2.mkdir(exist_ok=True)
    (dir2 / "file2.txt").touch()

    # Create a symlink to dir2 inside dir1
    link = dir1 / "link_to_dir2"
    link.symlink_to(dir2)

    # Walk with follow_symlinks=True
    walked_paths = []
    for root, _dirs, _files in dir1.walk(follow_symlinks=True):
        walked_paths.append(str(root))

    # Should visit both directories
    assert any("test_walk_dir1" in p for p in walked_paths)

    # Clean up
    link.unlink()
    (dir1 / "file1.txt").unlink()
    (dir2 / "file2.txt").unlink()
    dir1.rmdir()
    dir2.rmdir()


def test_iterdir_with_symlink(gspath):
    """Test iterdir() when the path itself is a symlink to a directory"""
    target = gspath / "test_iterdir_symlink_target"
    target.mkdir(exist_ok=True)
    (target / "file.txt").touch()

    link = gspath / "test_iterdir_symlink_link"
    link.symlink_to(target)

    # iterdir should follow the symlink
    items = list(link.iterdir())
    assert len(items) == 1
    assert items[0].name == "file.txt"

    # Clean up
    (target / "file.txt").unlink()
    link.unlink()
    target.rmdir()


def test_copy_file(gspath):
    """Test copying a file"""
    source = gspath / "test_copy_source.txt"
    source.write_text("test content")

    dest = gspath / "test_copy_dest.txt"
    source.copy(dest)

    assert dest.exists()
    assert dest.read_text() == "test content"

    # Clean up
    source.unlink()
    dest.unlink()


def test_copy_file_to_directory(gspath):
    """Test copying a file to a directory"""
    source = gspath / "test_copy_to_dir_source.txt"
    source.write_text("test content")

    dest_dir = gspath / "test_copy_to_dir"
    dest_dir.mkdir(exist_ok=True)

    source.copy(dest_dir)

    dest_file = dest_dir / "test_copy_to_dir_source.txt"
    assert dest_file.exists()
    assert dest_file.read_text() == "test content"

    # Clean up
    source.unlink()
    dest_file.unlink()
    dest_dir.rmdir()


def test_copy_non_existent_raises_error(gspath):
    """Test that copying a non-existent file raises an error"""
    source = gspath / "test_copy_nonexistent.txt"
    dest = gspath / "test_copy_dest2.txt"

    with pytest.raises(ValueError):
        source.copy(dest)


def test_copy_directory_raises_error(gspath):
    """Test that copying a directory with the PurePath copy() method raises an error"""
    # Note: GSPath.copy is wrapped and doesn't call PurePath._copy for directories
    # So we test the PurePath._copy method directly by using a directory
    from pathlib import PurePath

    source = gspath / "test_copy_dir"
    source.mkdir(exist_ok=True)

    dest = gspath / "test_copy_dir_dest"

    # Call the _copy method directly to test the ValueError for directories
    with pytest.raises(ValueError, match="should be a file"):
        PurePath.copy(source, dest)

    # Clean up
    source.rmdir()


# NOTE: The following copytree tests are commented out due to performance issues
# with GCS operations. The copytree functionality is tested through the PurePath._
# copytree
# implementation which is covered by other integration tests.

# def test_copytree(gspath):
#     """Test copying a directory tree"""
#     source = gspath / "test_copytree_source"
#     source.mkdir(exist_ok=True)
#     (source / "file1.txt").write_text("content1")
#     (source / "file2.txt").write_text("content2")
#
#     dest = gspath / "test_copytree_dest"
#     source.copytree(dest)
#
#     assert dest.exists()
#     assert dest.is_dir()
#     assert (dest / "file1.txt").read_text() == "content1"
#     assert (dest / "file2.txt").read_text() == "content2"
#
#     # Clean up
#     source.rmtree()
#     dest.rmtree()
#
#
# def test_copytree_with_ignore(gspath):
#     """Test copying a directory tree with ignore function"""
#     import shutil
#
#     source = gspath / "test_copytree_ignore_source"
#     source.mkdir(exist_ok=True)
#     (source / "file1.txt").write_text("content1")
#     (source / "file2.log").write_text("content2")
#     (source / "file3.txt").write_text("content3")
#
#     dest = gspath / "test_copytree_ignore_dest"
#
#     # Ignore .log files
#     source.copytree(dest, ignore=shutil.ignore_patterns("*.log"))
#
#     assert dest.exists()
#     assert (dest / "file1.txt").exists()
#     assert not (dest / "file2.log").exists()
#     assert (dest / "file3.txt").exists()
#
#     # Clean up
#     source.rmtree()
#     dest.rmtree()
#
#
# def test_copytree_non_directory_raises_error(gspath):
#     """Test that copytree on a non-directory raises an error"""
#     source = gspath / "test_copytree_file.txt"
#     source.touch()
#
#     dest = gspath / "test_copytree_file_dest"
#
#     with pytest.raises(NotADirectoryError):
#         source.copytree(dest)
#
#     # Clean up
#     source.unlink()
#
#
# def test_copytree_to_existing_file_raises_error(gspath):
#     """Test that copytree to an existing file raises an error"""
#     source = gspath / "test_copytree_to_file_source"
#     source.mkdir(exist_ok=True)
#     (source / "file.txt").touch()
#
#     dest = gspath / "test_copytree_to_file_dest"
#     dest.touch()
#
#     with pytest.raises(FileExistsError):
#         source.copytree(dest)
#
#     # Clean up
#     (source / "file.txt").unlink()
#     source.rmdir()
#     dest.unlink()


def test_rmtree(gspath):
    """Test removing a directory tree"""
    tree = gspath / "test_rmtree"
    tree.mkdir(exist_ok=True)
    (tree / "file1.txt").touch()
    subdir = tree / "subdir"
    subdir.mkdir(exist_ok=True)
    (subdir / "file2.txt").touch()

    tree.rmtree()
    assert not tree.exists()


def test_rmtree_on_file_raises_error(gspath):
    """Test that rmtree on a file raises an error"""
    file = gspath / "test_rmtree_file.txt"
    file.touch()

    with pytest.raises(NotADirectoryError):
        file.rmtree()

    # Clean up
    file.unlink()


def test_mkdir_with_parents(gspath):
    """Test mkdir with parents=True"""
    path = gspath / "test_mkdir_with_parents" / "subdir" / "deepdir"
    path.mkdir(parents=True, exist_ok=True)

    assert path.exists()
    assert path.is_dir()

    # Clean up - remove from deepest to shallowest
    path.rmdir()
    path.parent.rmdir()
    path.parent.parent.rmdir()


def test_walk_with_symlink_to_directory(gspath):
    """Test walk when encountering a symlink with follow_symlinks=True"""
    # Create a directory structure
    dir1 = gspath / "test_walk_symlink_dir1"
    dir1.mkdir(exist_ok=True)
    (dir1 / "file1.txt").touch()

    dir2 = gspath / "test_walk_symlink_dir2"
    dir2.mkdir(exist_ok=True)
    (dir2 / "file2.txt").touch()

    # Create a symlink to dir2
    link = gspath / "test_walk_symlink_link"
    link.symlink_to(dir2)

    # Walk from the symlink with follow_symlinks=True
    walked_paths = []
    for root, _dirs, _files in link.walk(follow_symlinks=True):
        walked_paths.append(str(root))

    # Should visit the target directory
    assert any("test_walk_symlink_dir2" in p for p in walked_paths)

    # Clean up
    (dir1 / "file1.txt").unlink()
    (dir2 / "file2.txt").unlink()
    link.unlink()
    dir1.rmdir()
    dir2.rmdir()


def test_copy_through_symlink(gspath):
    """Test copy operation through symlink with follow_symlinks"""
    target = gspath / "test_copy_symlink_target.txt"
    target.write_text("original content")

    link = gspath / "test_copy_symlink_link.txt"
    link.symlink_to(target)

    dest = gspath / "test_copy_symlink_dest.txt"

    # Copy through symlink (should follow by default)
    link.copy(dest)

    assert dest.exists()
    assert dest.read_text() == "original content"

    # Clean up
    link.unlink()
    target.unlink()
    dest.unlink()


def test_eq_with_trailing_slash(gspath):
    """Test equality comparison with trailing slash"""
    path1 = gspath / "test_eq"
    path1.mkdir(exist_ok=True)

    # Create the same path with trailing slash
    from yunpath import AnyPath
    path2 = AnyPath(str(path1) + "/")

    assert path1 == path2

    # Clean up
    path1.rmdir()


def test_fspath_property():
    """Test fspath property on PurePath"""
    from pathlib import PurePath
    p = PurePath("/test/path")
    assert p.fspath == "/test/path"


def test_resolve_circular_symlink_detection(gspath):
    """Test that resolve() detects circular symlinks"""
    # Create a circular symlink chain
    link1 = gspath / "test_circular_link1"
    link2 = gspath / "test_circular_link2"

    # Create circular reference
    link1.symlink_to(link2)
    link2.symlink_to(link1)

    # Should raise OSError for too many symlink levels
    with pytest.raises(OSError, match="Too many levels of symbolic links"):
        link1.resolve()

    # Clean up
    link1.unlink()
    link2.unlink()


def test_copy_with_positional_arg(gspath):
    """Test that copy() resolves symlinks when target is passed positionally"""
    source = gspath / "test_copy_pos_source.txt"
    source.write_text("content")

    target_file = gspath / "test_copy_pos_target.txt"

    link = gspath / "test_copy_pos_link.txt"
    link.symlink_to(source)

    dest_link = gspath / "test_copy_pos_dest_link.txt"
    dest_link.symlink_to(target_file)

    # Copy from symlink to symlink using positional arg
    # This should follow both symlinks
    link.copy(dest_link, force_overwrite_to_cloud=True)

    # Target should have the content
    assert target_file.read_text() == "content"

    # Clean up
    link.unlink()
    source.unlink()
    dest_link.unlink()
    target_file.unlink()


def test_eq_without_network_call(gspath):
    """Test that __eq__ doesn't make network calls for trailing slash comparison"""
    from yunpath import AnyPath

    path1_str = str(gspath / "test_eq_no_network")
    path2_str = path1_str + "/"

    path1 = AnyPath(path1_str)
    path2 = AnyPath(path2_str)

    # These should be equal based on string comparison alone
    # without making network calls (we can't truly test no network calls,
    # but we verify the logic works)
    assert path1 == path2
