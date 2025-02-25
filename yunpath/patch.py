"""Patch cloudpathlib to fix issues or add features"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Generator
from cloudpathlib.gs.gspath import GSPath
from cloudpathlib.gs.gsclient import GSClient
from cloudpathlib.exceptions import NoStatError


_original_is_file_or_dir = GSClient._is_file_or_dir


def _is_file_or_dir(self, cloud_path: GSPath) -> str | None:
    """Check if a path is a file or a directory"""
    out = _original_is_file_or_dir(self, cloud_path)
    if out is not None:
        return out

    prefix = cloud_path.blob.rstrip("/") + "/"
    placeholder_blob = self.client.bucket(cloud_path.bucket).get_blob(prefix)
    if placeholder_blob is not None:  # pragma: no cover
        return "dir"

    return None


def _move_file(
    self,
    src: GSPath,
    dst: GSPath,
    remove_src: bool = True,
) -> GSPath:   # pragma: no cover
    # patch: Just to replace deprecated utcnow
    # just a touch, so "REPLACE" metadata
    if src == dst:
        bucket = self.client.bucket(src.bucket)
        blob = bucket.get_blob(src.blob)

        # See
        # https://github.com/googleapis/google-cloud-python/issues/1185#issuecomment-431537214
        if blob.metadata is None:
            # patch, utcnow is deprecated
            blob.metadata = {"updated": datetime.now().isoformat()}
        else:
            blob.metadata["updated"] = datetime.now().isoformat()
        blob.patch()

    else:
        src_bucket = self.client.bucket(src.bucket)
        dst_bucket = self.client.bucket(dst.bucket)

        src_blob = src_bucket.get_blob(src.blob)
        src_bucket.copy_blob(src_blob, dst_bucket, dst.blob)

        if remove_src:
            src_blob.delete()

    return dst


GSClient._is_file_or_dir = _is_file_or_dir  # type: ignore[method-assign]
GSClient._move_file = _move_file  # type: ignore[method-assign]


def mkdir(self, parents: bool = False, exist_ok: bool = False):
    """Create a directory

    The original implementation of mkdir() in cloudpathlib does not support
    creating directories in Google Cloud Storage. This method is a patch to
    support creating directories in Google Cloud Storage

    Args:
        parents (bool, optional): If true, also create parent directories.
            Defaults to False.
        exist_ok (bool, optional): If true, do not raise an exception if
            the directory already exists. Defaults to False.
    """
    if self.exists():
        if not exist_ok:
            raise FileExistsError(f"cannot create directory '{self}': File exists")
        if not self.is_dir():  # pragma: no cover
            raise NotADirectoryError(
                f"cannot create directory '{self}': Not a directory"
            )
        return

    if parents:
        self.parent.mkdir(parents=True, exist_ok=True)
    elif not self.parent.exists():
        raise FileNotFoundError(
            f"cannot create directory '{self}': No such file or directory"
        )

    path = self.blob.rstrip("/") + "/"
    blob = self.client.client.bucket(self.bucket).blob(path)
    blob.upload_from_string("")


def __eq__(self, other: Any) -> bool:
    if not isinstance(other, type(self)):
        return False
    if str(self) == str(other):
        return True
    if self.is_dir() and str(self) == str(other).rstrip("/"):  # marked
        return True
    return False


def iterdir(self) -> Generator[GSPath, None, None]:
    """Iterate over the directory entries"""
    for f, _ in self.client._list_dir(self, recursive=False):
        if self == f:
            # originally f == self used, which cannot detect
            # the situation at the marked line in __eq__ method
            continue

        # If we are list buckets,
        # f = GSPath('gs://<Bucket: bucket_name>')
        if f.bucket.startswith("<Bucket: "):  # pragma: no cover
            yield GSPath(f.cloud_prefix + f.bucket[9:-1])
        else:
            yield f


def stat(self) -> os.stat_result:
    """Return the stat result for the path"""
    meta = self.client._get_metadata(self)

    # check if there is updated in the real metadata
    # if so, use it as mtime
    bucket = self.client.client.bucket(self.bucket)
    blob = bucket.get_blob(self.blob)
    if blob and blob.metadata and "updated" in blob.metadata:
        updated = blob.metadata["updated"]
        if isinstance(updated, str):
            updated = datetime.fromisoformat(updated)
        meta["updated"] = updated

    if meta is None:
        raise NoStatError(
            f"No stats available for {self}; it may be a directory or not exist."
        )

    try:
        mtime = meta["updated"].timestamp()
    except KeyError:  # pragma: no cover
        mtime = 0

    return os.stat_result(
        (
            None,  # mode
            None,  # ino
            self.cloud_prefix,  # dev,
            None,  # nlink,
            None,  # uid,
            None,  # gid,
            meta.get("size", 0),  # size,
            None,  # atime,
            mtime,  # mtime,
            None,  # ctime,
        )
    )


GSPath.mkdir = mkdir  # type: ignore[method-assign]
GSPath.__eq__ = __eq__  # type: ignore[assignment]
GSPath.iterdir = iterdir  # type: ignore[assignment]
GSPath.stat = stat  # type: ignore[assignment]
