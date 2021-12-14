# PDH - PagerDuty CLI for humans

![Build Image](https://github.com/mbovo/pdh/actions/workflows/build-image.yml/badge.svg)

See [docs](./docs)

## Usage

First of all you need to configure `pdh` to talk with PagerDuty APIs:

```bash
pdh config
```

Will ask you for 3 settings:

- `apiky` is the API key from the user's profile page on pagerduty
- `email` your pagerduty email
- `uid` the userID of your account (you can read it from the link address when clicking on "My Profile")

Settings are persisted to `~/.config/pdh.yaml`

### Listing incidents assigned to self

```bash
pdh inc ls
```

### Auto ACK incoming incidents

Watch for new incidents every 10s and automatically set them to Acknowledged

```bash
pdh inc ls --watch --new --ack --timeout 10
```

### List all HIGH priority incidents periodically

List incidents asssigned to all users every 5s

```bash
pdh inc ls --high --everything --watch --timeout 5
```

### Resolve specific incidents

```bash
pdh inc resolve INCID0001 INCID0024 INCID0023
```

## Resolve all incidents related to `Backups`

```bash
pdh inc ls --resolve --regexp ".*Backup.*"
```

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
