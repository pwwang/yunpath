from __future__ import annotations

import shutil
import sys
from functools import wraps
from pathlib import Path
from typing import Generator, List, Tuple, Callable
from cloudpathlib.cloudpath import CloudPath, CloudImplementation, CloudPathMeta
from cloudpathlib.azure import AzureBlobPath, AzureBlobClient
from cloudpathlib.s3 import S3Path, S3Client
from cloudpathlib.gs import GSPath, GSClient


_original_cloudpathmeta_call = CloudPathMeta.__call__


# allow default of cloud_path when YPath() is called
def _cloudpathmeta_call(cls, cloud_path=None, *args, **kwargs):
    """Call the CloudPathMeta class."""
    if cloud_path is None:
        return type.__call__(cls, ".", *args, **kwargs)

    return _original_cloudpathmeta_call(cls, cloud_path, *args, **kwargs)


CloudPathMeta.__call__ = _cloudpathmeta_call  # type: ignore[method-assign]


def _make_method(method: str, kind: str = "common") -> Callable:
    """Make a method that calls the method on the underlying class.

    Args:
        method (str): The name of the method to call.
        kind (str, optional): The kind of method to call. Defaults to "regular".
            - "common": Call the method on Path or CloudPath depending on the class.
            - "local_only": Call the method on Path only.
            - "cloud_only": Call the method on CloudPath only.
            - "cloud_always_false": Call the method on CloudPath and return False
                and Path as is.
            - "local_always_false": Call the method on Path and return False
                and CloudPath as is.
            - "returns_path": Call the method on Path or CloudPath depending
                on the class and return a YPath object.
    """
    pypath_method = getattr(Path, method)
    is_property = isinstance(pypath_method, property)

    if is_property:

        @property  # type: ignore[misc]
        @wraps(pypath_method)
        def _method(self):
            if kind == "cloud_always_false" and self._class != Path:
                # they are all non-properties for now
                return False  # pragma: no cover
            if kind == "local_always_false" and self._class == Path:
                return False  # pragma: no cover
            if kind == "local_only" and self._class != Path:
                raise NotImplementedError(
                    f"{method!r} is not supported for cloud paths"
                )
            if kind == "cloud_only" and self._class == Path:  # pragma: no cover
                raise NotImplementedError(
                    f"{method!r} is not supported for local paths"
                )

            the_method = (
                pypath_method
                if self._class == Path
                else getattr(self._class, method)
            )
            out = the_method.fget(self)

            if kind == "returns_path":
                return self.__class__(out)

            return out

    else:

        @wraps(pypath_method)
        def _method(self, *args, **kwargs):
            if kind == "cloud_always_false" and self._class != Path:
                return False
            if kind == "local_always_false" and self._class == Path:
                return False  # pragma: no cover
            if kind == "local_only" and self._class != Path:
                raise NotImplementedError(
                    f"{method!r} is not supported for cloud paths"
                )
            if kind == "cloud_only" and self._class == Path:
                raise NotImplementedError(  # pragma: no cover
                    f"{method!r} is not supported for local paths"
                )

            the_method = (
                pypath_method
                if self._class == Path
                else getattr(self._class, method)
            )
            out = the_method(self, *args, **kwargs)

            if kind == "returns_path":
                return self.__class__(out)

            return out

    return _method


def blend_methods(cls):
    """Blend the methods of Path and CloudPath into a single class."""

    methods = [
        (method,)
        for method in dir(Path)
        if method in dir(CloudPath)
        and method
        not in [
            "__class__",
            "__init__",
            "__new__",
            "__getattribute__",
            "__setattr__",
            "__subclasshook__",
            "iterdir",
            "parent",
            "parents",
            "walk",
            "full_match",
            "from_uri",
        ]
    ] + [
        ("chmod", "local_only"),
        ("lchmod", "local_only"),
        ("lstat", "local_only"),
        ("expanduser", "local_only"),
        ("group", "local_only"),
        ("owner", "local_only"),
        ("readlink", "local_only"),
        ("symlink_to", "local_only"),
        ("hardlink_to", "local_only"),
        ("root", "local_only"),
        ("rename", "returns_path"),
        ("replace", "returns_path"),
        ("resolve", "returns_path"),
        ("with_name", "returns_path"),
        ("with_segments", "returns_path"),
        ("with_suffix", "returns_path"),
        ("with_stem", "returns_path"),
        ("joinpath", "returns_path"),
        ("parent", "returns_path"),
        ("__truediv__", "returns_path"),
        ("__rtruediv__", "returns_path"),
        ("is_mount", "cloud_always_false"),
        ("is_symlink", "cloud_always_false"),
        ("is_socket", "cloud_always_false"),
        ("is_fifo", "cloud_always_false"),
        ("is_block_device", "cloud_always_false"),
        ("is_char_device", "cloud_always_false"),
    ]
    for method in methods:
        setattr(cls, method[0], _make_method(*method))

    return cls


@blend_methods
class YPath(Path, CloudPath):  # type: ignore[misc]
    """A path that can be either a local path or a cloud path."""

    def __init__(self, *args, **kwargs):

        if args and (
            isinstance(args[0], GSPath)
            or (isinstance(args[0], YPath) and args[0]._class == GSPath)
            or (isinstance(args[0], str) and args[0].startswith("gs://"))
        ):
            self._class = GSPath
            client_class = GSClient

        elif args and (
            isinstance(args[0], S3Path)
            or (isinstance(args[0], YPath) and args[0]._class == S3Path)
            or (isinstance(args[0], str) and args[0].startswith("s3://"))
        ):  # pragma: no cover
            self._class = S3Path
            client_class = S3Client

        elif args and (
            isinstance(args[0], AzureBlobPath)
            or (isinstance(args[0], YPath) and args[0]._class == AzureBlobPath)
            or (isinstance(args[0], str) and args[0].startswith("az://"))
        ):  # pragma: no cover
            self._class = AzureBlobPath
            client_class = AzureBlobClient

        else:
            self._class = Path

        if self._class != Path:
            self.__class__.cloud_prefix = self._class.cloud_prefix
            impl = CloudImplementation()
            impl._path_class = self._class
            impl._client_class = client_class
            self.__class__._cloud_meta = impl

        self._class.__init__(self, *args, **kwargs)

    blob = property(lambda self: self._class.blob.fget(self))
    bucket = property(lambda self: self._class.bucket.fget(self))
    client = property(lambda self: self._class.client.fget(self))

    @classmethod
    @wraps(Path.cwd)
    def cwd(cls):
        """Return the current working directory."""
        return cls(Path.cwd())

    @classmethod
    @wraps(Path.home)
    def home(cls):
        """Return the home directory."""
        return cls(Path.home())

    @classmethod
    def from_uri(cls, uri: str) -> YPath:
        """ "Return a new path from the given file or cloud URI."""
        if uri.startswith("file:"):
            if sys.version_info >= (3, 13):  # pragma: no cover
                # Python 3.13+ has a from_uri method
                return cls(Path.from_uri(uri))

            # implementation for Python 3.12 and below
            # we need to remove the 'file:' prefix and
            # merge multiple / into a single / at the beginning
            path = Path(uri[5:])
            if not path.is_absolute():
                raise ValueError(f"URI is not absolute: {uri!r}")

            return cls("/" + str(path).lstrip("/"))

        if (
            uri.startswith("gs://")
            or uri.startswith("s3://")
            or uri.startswith("az://")
        ):
            return cls(uri)

        raise ValueError(
            f"URI does not start with 'file:', 'gs:', 's3:', or 'az:': {uri!r}"
        )

    @property
    def is_cloud(self) -> bool:
        """True if the path is a cloud path.

        Returns:
            bool: True if the path is a cloud path.
        """
        return self._class != Path

    @property
    def is_local(self) -> bool:
        """True if the path is a local path.

        Returns:
            bool: True if the path is a local path.
        """
        return not self.is_cloud

    @wraps(Path.iterdir)
    def iterdir(self) -> Generator[YPath, None, None]:  # type: ignore
        """Iterate over the directory entries."""
        out = self._class.iterdir(self)
        for p in out:
            yield self.__class__(p)

    @wraps(Path.walk)
    def walk(  # type: ignore
        self, *args, **kwargs
    ) -> Generator[Tuple[YPath, List[str], List[str]], None, None]:
        out = self._class.walk(self)
        for p, dirs, files in out:
            yield self.__class__(p), dirs, files

    @property
    @wraps(Path.parents)
    def parents(self) -> List[YPath]:
        """Return a list of the path's parent directories."""
        return [self.__class__(p) for p in self._class.parents.fget(self)]

    def rmtree(self):
        """Remove the path and all its contents."""
        if self.is_cloud:
            self._class.rmtree(self)
        else:
            shutil.rmtree(self)

    def full_match(self, pattern, case_sensitive=None):
        """Return True if the path matches the pattern fully."""
        if sys.version_info < (3, 13):
            raise NotImplementedError("full_match requires Python 3.13 or higher")

        return self._class.full_match(  # pragma: no cover
            self,
            pattern,
            case_sensitive=case_sensitive,
        )

    def __del__(self):
        if self.is_cloud:
            self._class.__del__(self)
