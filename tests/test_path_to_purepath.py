import pytest
from yunpath import AnyPath


def test_rmtree(tmp_path):
    # Create a directory for testing
    test_dir = AnyPath(tmp_path) / "test_dir"
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "test_file"
    test_file.touch()

    with pytest.raises(NotADirectoryError):
        test_file.rmtree()

    test_dir.rmtree()
    assert not test_dir.exists()


def test_copy_self_not_exists(tmp_path):
    test_file = AnyPath(tmp_path) / "test_file"
    destination = AnyPath(tmp_path) / "destination"

    with pytest.raises(ValueError):
        test_file.copy(destination)


def test_copy_to_file(tmp_path):
    test_file = AnyPath(tmp_path) / "test_file"
    test_file.touch()
    destination = AnyPath(tmp_path) / "destination_file"

    test_file.copy(destination)
    assert destination.exists()
    assert destination.is_file()


def test_copy_to_dir(tmp_path):
    test_file = AnyPath(tmp_path) / "test_file"
    test_file.touch()
    destination_dir = AnyPath(tmp_path) / "destination_dir"
    destination_dir.mkdir(exist_ok=True)

    test_file.copy(destination_dir)
    copied_file = destination_dir / "test_file"
    assert copied_file.exists()
    assert copied_file.is_file()


def test_copy_to_cloudfile(tmp_path, gspath):
    test_file = AnyPath(tmp_path) / "test_file"
    test_file.touch()
    destination = gspath / "copy_destination_file"

    test_file.copy(destination, force_overwrite_to_cloud=True)
    assert destination.exists()
    assert destination.is_file()


def test_copy_to_clouddir(tmp_path, gspath):
    test_file = AnyPath(tmp_path) / "test_file"
    test_file.touch()
    destination_dir = gspath / "copy_destination_dir"
    destination_dir.mkdir(exist_ok=True)

    test_file.copy(destination_dir, force_overwrite_to_cloud=True)
    copied_file = destination_dir / "test_file"
    assert copied_file.exists()
    assert copied_file.is_file()


def test_copytree_self_not_dir(tmp_path):
    test_file = AnyPath(tmp_path) / "test_file"
    test_file.touch()
    destination = AnyPath(tmp_path) / "destination_dir"

    with pytest.raises(NotADirectoryError):
        test_file.copytree(destination)


def test_copytree_to_file(tmp_path):
    test_dir = AnyPath(tmp_path) / "test_dir"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "file1").touch()
    destination_file = AnyPath(tmp_path) / "destination_file"
    destination_file.touch()

    with pytest.raises(FileExistsError):
        test_dir.copytree(destination_file)


def test_copytree_to_dir(tmp_path):
    test_dir = AnyPath(tmp_path) / "test_dir"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "file1").touch()
    (test_dir / "subdir").mkdir(exist_ok=True)
    (test_dir / "subdir" / "file2").touch()
    destination_dir = AnyPath(tmp_path) / "destination_dir"

    test_dir.copytree(destination_dir)
    assert destination_dir.exists()
    assert destination_dir.is_dir()
    assert (destination_dir / "file1").exists()
    assert (destination_dir / "subdir").exists()
    assert (destination_dir / "subdir").is_dir()
    assert (destination_dir / "subdir" / "file2").exists()


def test_copytree_ignore(tmp_path):
    test_dir = AnyPath(tmp_path) / "test_dir"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "file1").touch()
    (test_dir / "file2").touch()
    (test_dir / "subdir").mkdir(exist_ok=True)
    (test_dir / "subdir" / "file3").touch()
    destination_dir = AnyPath(tmp_path) / "destination_dir"

    def ignore_func(dir, files):
        return {"file2", "subdir"}

    test_dir.copytree(destination_dir, ignore=ignore_func)
    assert destination_dir.exists()
    assert destination_dir.is_dir()
    assert (destination_dir / "file1").exists()
    assert not (destination_dir / "file2").exists()
    assert not (destination_dir / "subdir").exists()


def test_copytree_to_clouddir(tmp_path, gspath):
    test_dir = AnyPath(tmp_path) / "test_dir"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "file1").touch()
    (test_dir / "subdir").mkdir(exist_ok=True)
    (test_dir / "subdir" / "file2").touch()
    destination_dir = gspath / "destination_dir"

    test_dir.copytree(destination_dir, force_overwrite_to_cloud=True)
    assert destination_dir.exists()
    assert destination_dir.is_dir()
    assert (destination_dir / "file1").exists()
    assert (destination_dir / "subdir").exists()
    assert (destination_dir / "subdir").is_dir()
    assert (destination_dir / "subdir" / "file2").exists()
