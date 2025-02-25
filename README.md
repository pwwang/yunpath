# yunpath

`Yun` (`云`) is the Chinese word for `cloud`. `yunpath` is a Python library that extends the `pathlib` library to support cloud storage services.

## Credits

This library is a wrapper around the [`cloudpathlib`][1] library.

## Installation

```bash
pip install yunpath
```

## Usage

```python
from yunpath import YPath

path = YPath("/local/path")

path.is_local # True
path.is_cloud # False

path = YPath("gs://bucket/path")

path.is_local # False
path.is_cloud # True

# Then use the APIs like pathlib.Path
```

[1]: https://github.com/drivendataorg/cloudpathlib
