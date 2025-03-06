from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import PurePath

from cloudpathlib.client import register_client_class
from cloudpathlib.exceptions import NoStatError
from cloudpathlib.gs.gsclient import GSClient as _GSClient
from cloudpathlib.gs.gspath import GSPath as _GSPath
from cloudpathlib.cloudpath import register_path_class


def _rmtree(self, ignore_errors=False, onerror=None):
    """Recursively delete a directory tree."""
    if self.is_dir():
        shutil.rmtree(self, ignore_errors=ignore_errors, onerror=onerror)
    else:
        raise NotADirectoryError(f"[Errno 20] Not a directory: '{self}'")


PurePath.rmtree = _rmtree
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


@register_path_class("gs")
class GSPath(_GSPath):

    def mkdir(self, parents: bool = False, exist_ok: bool = False):
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

    def stat(self):
        """Return the stat result for the path"""
        meta = self.client._get_metadata(self)

        # check if there is updated in the real metadata
        # if so, use it as mtime
        bucket = self.client.client.bucket(self.bucket)
        blob = bucket.get_blob(self.blob)
        if blob and blob.metadata and "updated" in blob.metadata:  # pragma: no cover
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

        return os.stat_result(  # type: ignore[arg-type]
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
