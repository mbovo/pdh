# PDH - PagerDuty CLI for humans

![Build Image](https://github.com/mbovo/pdh/actions/workflows/build-image.yml/badge.svg)

`PDH` is a new lightweight CLI for pagerduty interaction: uou can handle your incidents triage without leaving your terminal.
It also add some nice tricks to automate the incident triage and easy the on-call burden.

See [docs](./docs) (TBD)

## Install

### Nix

If you are using [cachix](https://cachix.org) you can use the prebuilt packages:

```bash
cachix use pdh
```

```bash
nix shell github:mbovo/pdh
```

### Arch linux

```bash
yay -S pdh
```

### With docker

```bash
docker run -ti -v ~/.config/pdh.yaml:/root/.config/pdh.yaml --rm pdh:0.3.10 inc ls
```

### With pip

```bash
pip install pdh>=0.3.10
```

### From source with nix and direnv

```bash

git clone https://github.com/mbovo/pdh
direnv allow pdh
cd pdh
pdh inc ls -e
```

### From source with devbox

```bash
git clone https://github.com/mbovo/pdh
direnv allow pdh
cd pdh
pdh inc ls -e

```

### From source

```bash
git clone https://github.com/mbovo/pdh
cd pdh
task setup
source .venv/bin/activate
pdh inc ls -e
```

## Usage

First of all you need to configure `pdh` to talk with PagerDuty's APIs:

```bash
pdh config
```

The wizard will prompt you for 3 settings:

- `apikey` is the API key, you can generate it from the user's profile page on pagerduty website
- `email` the email address of your pagerduty profile
- `uid` the userID of your account (you can read it from the browser address bar when clicking on "My Profile")

Settings are persisted to `~/.config/pdh.yaml` in clear.

### Listing incidents

Assigned to self:

```bash
pdh inc ls
```

Any other incident currently outstanding:

```bash
pdh inc ls -e
```

### Auto ACK incoming incidents

Watch for new incidents every 10s and automatically set them to `Acknowledged`

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

### Resolve all incidents related to `Backups`

```bash
pdh inc ls --resolve --regexp ".*Backup.*"
```

## Rules

`PDH` support custom scripting applied to your incidents list. These `rules` are in fact any type of executable you can run on your machine.

```bash
pdh inc apply INCID001 -s /path/to/my/script.py -s /path/to/binary
```

The `apply` subcommand will call the listed executable/script passing along a json to stdin with the incident informations. The called script can apply any type of checks/sideffects and output another json to stout to answer the call.

Even though rules can be written in any language it's very straightforward using python:

### Rules: an example

An example rule can be written in python with the following lines

```python
#!/usr/bin/env python3
from pdh import rules, Filter

@rules.rule
def main(input):
    return {i["id"]: i["summary"] for i in input}

if __name__ == "__main__":
    main()
```

This is the simplest rule you can write, reading the input and simply output a new dictionary with the entries. It will output something like:

```bash

 pdh inc apply Q1LNI5LNM7RZ2C Q1C5KG41H0SZAM -s ./a.py
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ script ┃ Q1LNI5LNM7RZ2C                                                     ┃ Q1C5KG41H0SZAM                                                                       ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ./a.py │  AWS Health Event: us-east-1 EC2 : AWS_EC2_INSTANCE_STOP_SCHEDULED │  AWS Health Event: us-east-1 EC2 : AWS_EC2_INSTANCE_STORE_DRIVE_PERFORMANCE_DEGRADED │
└────────┴────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────┘
```

The default output is `table` with one line for each script runned and with one column per each element in the returned object

### Rules: more examples

```python
#!/usr/bin/env python3

# Needed imports
from pdh import rules, Filter

# This annotation make the main() method parse stdin as json into the parameter called input
# All returned values are converted to json and printed to stdout
@rules.rule
def main(input):

    # Initialize PagerDuty's APIs
    api = rules.api()

    # From the given input extract only incidents with the word cassandra in title
    incs = Filter.objects(input, filters=[Filter.regexp("title", ".*EC2.*")])

    # ackwnoledge all previously filtered incidents
    api.ack(incs)

    # resolve all previously filtered incidents
    api.resolve(incs)

    # snooze all previously filtered incidents for 1h
    api.snooze(incs, duration=3600)

    # Chain a given rule, i.e call that rule with the output of this one
    # chain-loading supports only a single binary, not directories
    c = rules.chain(incs, "rules/test_chaining.sh")

    # Execute an external program and get the output/err/return code
    p: rules.ShellResponse = rules.exec('kubectl get nodes -o name')
    if p.rc > 0:
      nodes = p.stdout.split("\n")

    # if you return a dict will be rendered with each item as a column in a table
    # Othrwise will be converted as string
    return {i["id"]: i["summary"] for i in incs}


if __name__ == "__main__":
    main()


```

## Requirements

- [Taskfile](https://taskfile.dev)
- Python >=3.10
- Docker

## Contributing

First of all you need to setup the dev environment, using Taskfile:

```bash
task setup
```

This will create a python virtualenv and install `pre-commit` and `poetry` in your system if you lack them.


## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
See [](LICENSE) for more details.
