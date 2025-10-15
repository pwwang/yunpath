from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import PurePath
from typing import Callable, Container, Iterable

from cloudpathlib.client import register_client_class
from cloudpathlib.exceptions import (
    CloudPathFileExistsError,
    CloudPathNotExistsError,
    CloudPathIsADirectoryError,
    NoStatError,
)
from cloudpathlib.gs.gsclient import GSClient as _GSClient
from cloudpathlib.gs.gspath import GSPath as _GSPath
from cloudpathlib.cloudpath import register_path_class, CloudPath
from cloudpathlib.anypath import to_anypath


def _rmtree(self, ignore_errors=False, onerror=None):
    """Recursively delete a directory tree."""
    if self.is_dir():
        shutil.rmtree(self, ignore_errors=ignore_errors, onerror=onerror)
    else:
        raise NotADirectoryError(f"[Errno 20] Not a directory: '{self}'")


def _copy(
    self,
    destination: str | os.PathLike | CloudPath,
    force_overwrite_to_cloud: bool | None = None,
):
    """Copy a file to a destination."""
    if not self.exists() or not self.is_file():
        raise ValueError(
            f"Path {self} should be a file. To copy a directory tree use "
            "the method copytree."
        )

    # handle string version of cloud paths + local paths
    if isinstance(destination, (str, os.PathLike)):
        destination = to_anypath(destination)

    if destination.is_dir():
        destination = destination / self.name

    if not isinstance(destination, CloudPath):
        return shutil.copyfile(self, destination)

    else:
        return destination.upload_from(
            self, force_overwrite_to_cloud=force_overwrite_to_cloud
        )


def _copytree(
    self,
    destination: str | os.PathLike | CloudPath,
    follow_symlinks: bool = True,  # not used  # noqa
    force_overwrite_to_cloud: bool | None = None,
    ignore: Callable[[str, Iterable[str]], Container[str]] | None = None,
):
    """Recursively copy a directory tree to a destination directory."""
    if not self.is_dir():
        raise NotADirectoryError(
            f"Origin path {self} must be a directory. "
            "To copy a single file use the method copy."
        )

    # handle string version of cloud paths + local paths
    if isinstance(destination, (str, os.PathLike)):
        destination = to_anypath(destination)

    if destination.exists() and destination.is_file():
        raise FileExistsError(
            f"Destination path {destination} of copytree must be a directory."
        )

    contents = list(self.iterdir())

    if ignore is not None:
        ignored_names = ignore(self, [x.name for x in contents])
    else:
        ignored_names = set()

    destination.mkdir(parents=True, exist_ok=True)

    for subpath in contents:
        if subpath.name in ignored_names:
            continue
        if subpath.is_file():
            subpath.copy(
                destination / subpath.name,
                force_overwrite_to_cloud=force_overwrite_to_cloud,
            )
        elif subpath.is_dir():
            subpath.copytree(
                destination
                / (subpath.name + ("" if subpath.name.endswith("/") else "/")),
                force_overwrite_to_cloud=force_overwrite_to_cloud,
                ignore=ignore,
            )

    return destination


PurePath.rmtree = _rmtree
PurePath.copy = _copy
PurePath.copytree = _copytree
PurePath.fspath = property(lambda self: str(self))


@register_client_class("gs")
class GSClient(_GSClient):

    def _is_file_or_dir(self, cloud_path: _GSPath) -> str | None:
        """Check if a path is a file or a directory"""
        out = super()._is_file_or_dir(cloud_path)
        if out is not None and out != "file":
            return out

        prefix = cloud_path.blob.rstrip("/") + "/"
        placeholder_blob = self.client.bucket(cloud_path.bucket).get_blob(prefix)
        if placeholder_blob is not None:  # pragma: no cover
            return "dir"

        return out


def _wrap_follow_symlinks(
    method: Callable,
    target_argname: str | None = None,
) -> Callable:
    def wrapper(self, *args, follow_symlinks=True, **kwargs):
        if follow_symlinks:
            path = self.resolve()
            if target_argname is not None and target_argname in kwargs:
                target = to_anypath(kwargs[target_argname])
                kwargs[target_argname] = target.resolve()
        else:
            path = self

        return method(path, *args, **kwargs)

    return wrapper


@register_path_class("gs")
class GSPath(_GSPath):

    def mkdir(self, parents: bool = False, exist_ok: bool = False):
        if self.exists():
            if not exist_ok:
                raise CloudPathFileExistsError(
                    f"cannot create directory '{self}': File exists"
                )
            if not self.is_dir():  # pragma: no cover
                raise CloudPathIsADirectoryError(
                    f"cannot create directory '{self}': Not a directory"
                )
            return

        if parents:
            self.parent.mkdir(parents=True, exist_ok=True)
        elif not self.parent.exists():
            raise CloudPathNotExistsError(
                f"cannot create directory '{self}': No such file or directory"
            )

        path = self.blob.rstrip("/") + "/"
        blob = self.client.client.bucket(self.bucket).blob(path)
        blob.upload_from_string("")

    def walk(
        self,
        top_down: bool = True,
        on_error: Callable | None = None,
        follow_symlinks: bool = False,
    ):
        if follow_symlinks and self.is_symlink():
            path = self.resolve()
        else:
            path = self

        yield from super(GSPath, path).walk(
            top_down=top_down, on_error=on_error, follow_symlinks=False
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        if str(self) == str(other):
            return True
        if str(self) == str(other).rstrip("/") and self.is_dir():  # marked
            return True
        return False

    def iterdir(self):
        """Iterate over the directory entries"""
        if self.is_symlink():
            path = self.resolve()
        else:
            path = self

        for f, _ in self.client._list_dir(path, recursive=False):
            if path == f:
                # originally f == self used, which cannot detect
                # the situation at the marked line in __eq__ method
                continue

            # If we are list buckets,
            # f = GSPath('gs://<Bucket: bucket_name>')
            if f.bucket.startswith("<Bucket: "):  # pragma: no cover
                yield GSPath(f.cloud_prefix + f.bucket[9:-1], client=self.client)
            else:
                yield f

    def stat(self, follow_symlinks: bool = True) -> os.stat_result:
        """Return the stat result for the path"""
        if follow_symlinks and self.is_symlink():
            path = self.resolve()
        else:
            path = self

        meta = path.client._get_metadata(path)

        # check if there is updated in the real metadata
        # if so, use it as mtime
        bucket = path.client.client.bucket(path.bucket)
        blob = bucket.get_blob(path.blob)
        if blob and blob.metadata and "updated" in blob.metadata:  # pragma: no cover
            updated = blob.metadata["updated"]
            if isinstance(updated, str):
                updated = datetime.fromisoformat(updated)
            meta["updated"] = updated

        if meta is None:
            raise NoStatError(
                f"No stats available for {path}; it may be a directory or not exist."
            )

        try:
            mtime = meta["updated"].timestamp()
        except KeyError:  # pragma: no cover
            mtime = 0

        return os.stat_result(  # type: ignore[arg-type]
            (
                None,  # mode
                None,  # ino
                path.cloud_prefix,  # dev,
                None,  # nlink,
                None,  # uid,
                None,  # gid,
                meta.get("size", 0),  # size,
                None,  # atime,
                mtime,  # mtime,
                None,  # ctime,
            )
        )

    def is_symlink(self) -> bool:
        """Check if it is a gcsfuse created symlink"""
        if not self.blob:
            # root bucket
            return False

        blob = self.client.client.bucket(self.bucket).get_blob(self.blob)
        return (
            blob
            and blob.metadata
            and isinstance(blob.metadata, dict)
            and "gcsfuse_symlink_target" in blob.metadata
        )

    def readlink(self) -> GSPath:
        """Read the target of a gcsfuse created symlink"""
        if not self.is_symlink():
            raise OSError(f"{self} is not a symlink")

        blob = self.client.client.bucket(self.bucket).get_blob(self.blob)
        assert blob is not None and blob.metadata is not None  # for mypy
        target = blob.metadata["gcsfuse_symlink_target"]
        if target.startswith("gs://"):
            return GSPath(target, client=self.client)
        return self.parent / target

    def resolve(self, strict: bool = False) -> GSPath:
        """Make the path absolute, resolving any symlinks.

        If strict is True, raise an exception if the path doesn't exist.
        """
        if not self.exists(follow_symlinks=False) and strict:
            raise CloudPathNotExistsError(f"Path {self} does not exist.")

        allparts = list(self.parts)
        resolved = False
        max_iterations = 100  # Prevent infinite loops with circular symlinks
        iterations = 0

        while not resolved and iterations < max_iterations:
            iterations += 1
            resolved = True
            parts = ["gs://"]

            for i, part in enumerate(allparts[1:], start=1):
                parts.append(part)
                current_path = GSPath(*parts, client=self.client)

                if current_path.is_symlink():
                    target = current_path.readlink()
                    # Replace current path with target and append remaining parts
                    allparts = list(target.parts) + allparts[i + 1 :]
                    resolved = False
                    break

        return GSPath(*allparts, client=self.client)

    def symlink_to(self, target: str | os.PathLike | CloudPath) -> GSPath:
        """Create a gcsfuse compatible symlink to target named self."""
        if self.exists(follow_symlinks=False):
            raise CloudPathFileExistsError(
                f"Path {self} already exists. Cannot create link."
            )

        blob = self.client.client.bucket(self.bucket).blob(self.blob)
        metadata = {"gcsfuse_symlink_target": str(target)}
        blob.metadata = metadata
        blob.upload_from_string("")

        return self

    def unlink(self, missing_ok: bool = True) -> None:
        if self.is_dir(follow_symlinks=False):
            raise CloudPathIsADirectoryError(
                f"Path {self} is a directory; call rmdir instead of unlink."
            )
        self.client._remove(self, missing_ok)

    exists = _wrap_follow_symlinks(_GSPath.exists)
    is_dir = _wrap_follow_symlinks(_GSPath.is_dir)
    is_file = _wrap_follow_symlinks(_GSPath.is_file)
    copy = _wrap_follow_symlinks(_GSPath.copy, target_argname="target")
    copyinfo = _wrap_follow_symlinks(_GSPath.copy_into, target_argname="target_dir")
    copytree = _wrap_follow_symlinks(_GSPath.copytree, target_argname="target_dir")
    move = _wrap_follow_symlinks(_GSPath.move, target_argname="target")
    moveinto = _wrap_follow_symlinks(_GSPath.move_into, target_argname="target_dir")
    open = _wrap_follow_symlinks(_GSPath.open)
    read_bytes = _wrap_follow_symlinks(_GSPath.read_bytes)
    read_text = _wrap_follow_symlinks(_GSPath.read_text)
    write_bytes = _wrap_follow_symlinks(_GSPath.write_bytes)
    write_text = _wrap_follow_symlinks(_GSPath.write_text)
    rmdir = _wrap_follow_symlinks(_GSPath.rmdir)
    rmtree = _wrap_follow_symlinks(_GSPath.rmtree)
    samefile = _wrap_follow_symlinks(_GSPath.samefile, target_argname="other_path")
