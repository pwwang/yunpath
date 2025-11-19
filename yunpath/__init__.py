import sys

# FutureWarning: You are using a Python version (3.10.19) which Google will stop
# supporting in new releases of google.api_core once it reaches its end of life
# (2026-10-04).
# Please upgrade to the latest Python version, or at least Python 3.11,
# to continue receiving updates for google.api_core past that date.
if sys.version_info < (3, 11):  # pragma: no cover
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning)

from cloudpathlib.anypath import AnyPath
from cloudpathlib.azure.azblobclient import AzureBlobClient
from cloudpathlib.azure.azblobpath import AzureBlobPath
from cloudpathlib.cloudpath import CloudPath, implementation_registry
from cloudpathlib.s3.s3client import S3Client
from cloudpathlib.s3.s3path import S3Path
from .patch import GSPath, GSClient

__all__ = [
    "AnyPath",
    "AzureBlobClient",
    "AzureBlobPath",
    "CloudPath",
    "implementation_registry",
    "GSClient",
    "GSPath",
    "S3Client",
    "S3Path",
]

__version__ = "0.1.0"
