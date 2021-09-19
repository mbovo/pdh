# PDH - PagerDuty CLI for humans

![Build Image](https://github.com/mbovo/pdh/actions/workflows/build-image.yml/badge.svg)


See [docs](./docs)

## Requirements

- [Taskfile](https://taskfile.dev)
- Python >=3.9
- Docker

## Contributing

First of all you need to setup the dev environment, using Taskfile:

```bash
task setup
```

This will create a python virtualenv and install `pre-commit` and `poetry` in your system if you lack them.
