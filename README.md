# PDH - PagerDuty CLI for humans

[![Tag and build](https://github.com/mbovo/pdh/actions/workflows/build-release.yml/badge.svg)](https://github.com/mbovo/pdh/actions/workflows/build-release.yml) [![Nix](https://github.com/mbovo/pdh/actions/workflows/nix.yml/badge.svg)](https://github.com/mbovo/pdh/actions/workflows/nix.yml)

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

#### Listing incident by team

Listing only outstanding alerts only if they are assigned to a specific team:

```bash
pdh inc ls -e --teams mine
```

Search for a given team id:

```bash
pdh teams ls
```

Use specific id (list):

```bash
pdh inc ls -e --team-id "P1LONJG,P4SEF5R"
```

### Sorting incident by field

```bash
pdh inc ls --sort assignee --reverse
```

In case the field is not found the cli will notice you and print the list of available fields

```bash
 pdh inc ls -e --sort unkn --reverse
Invalid sort field: unkn
Available fields: id, assignee, title, status, created_at, last_status_change_at, url
```

You can always sort by multiple fields using comma as separator:

```bash
pdh inc ls --sort assignee,status
```

### Auto ACK incoming incidents

Watch for new incidents every 10s and automatically set them to `Acknowledged`

```bash
pdh inc ls --watch --new --ack --timeout 10
```

### List all HIGH priority incidents periodically

List incidents assigned to all users every 5s

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

### Extract custom fields

You can also extract custom fields from the pagerduty json output:

You can nested fields using dot notation (i.e `service.summary`)

```bash
pdh inc ls -e --fields service.summary,status,title,assignee,created_at,url
```

To understand the available fields you can get the raw json output and inspect it:

```bash
pdh inc ls -e -o raw
```


## Rules

`PDH` support custom scripting applied to your incidents list. These `rules` are in fact any type of executable you can run on your machine.

```bash
pdh inc ls -e --rules-path ./rules/ --rules
```

The `apply` subcommand will call the listed executable/script passing along a json to stdin with the incident information. The called script can apply any type of checks/sideffects and output another json to stout to answer the call.

Even though rules can be written in any language it's very straightforward using python:

### Rules: an example

An example rule can be written in python with the following lines

```python
#!/usr/bin/env python3
from pdh.rules import rule

@rule
def main(alerts, pagerduty, Filters, Transformations):

    # From the given input extract only incidents with the word "EC2" in title
    filtered = Filters.apply(alerts, filters=[
                    Filters.not_regexp("service.summary", ".*My Service.*"),
                    Filters.regexp("title", ".*EC2.*")
                ])

    # # auto acknowledge all previously filtered incidents
    pagerduty.incidents.ack(filtered)

    return filtered

if __name__ == "__main__":
    main()                  # type: ignore
```


```bash

 pdh inc ls -e --rules-path ./rules/ --rules
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ script ┃ Q1LNI5LNM7RZ2C                                                     ┃ Q1C5KG41H0SZAM                                                                       ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ./a.py │  AWS Health Event: us-east-1 EC2 : AWS_EC2_INSTANCE_STOP_SCHEDULED │  AWS Health Event: us-east-1 EC2 : AWS_EC2_INSTANCE_STORE_DRIVE_PERFORMANCE_DEGRADED │
└────────┴────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────┘
```

The default output is `table` with one line for each script run and with one column per each element in the returned object

### Rules: more examples

see [rules](./rules) for more

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
