# yunpath

`Yun` (`云`) is the Chinese word for `cloud`. `yunpath` is a Python library that extends the `pathlib` library to support cloud storage services.

## Credits

This library is a wrapper around the [`cloudpathlib`][1] library.

## Installation

```bash
pip install yunpath
```

## Features

- Add `rmtree` to `pathlib.PurePath` to match the `cloudpathlib.CloudPath` API.
- Add `fspath` to `pathlib.PurePath` to match the `cloudpathlib.CloudPath` API.
- Allow to `mkdir` for `GSPath` objects.

[1]: https://github.com/drivendataorg/cloudpathlib
