import uuid
import pytest
from dotenv import load_dotenv
from yunpath import AnyPath

load_dotenv()


@pytest.fixture(scope="session")
def uid():
    return str(uuid.uuid4())


@pytest.fixture(scope="module")
def gspath(uid):  # noqa: F811
    """Return a AnyPath object"""
    p = AnyPath(
        f"gs://handy-buffer-287000.appspot.com/yunpath-test/test-{uid}"
    )
    p.mkdir(exist_ok=True)
    yield p
    p.rmtree()
