import uuid
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="session")
def uid():
    return str(uuid.uuid4())
