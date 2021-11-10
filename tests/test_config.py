from json.decoder import JSONDecodeError
from pdh import config
import tempfile
import json
import yaml

valid_config = {
    "apikey": "APIKEY",
    "uid": "UID",
    "email": "email@email.tld",
}

invalid_config = {
    "apikey": "APIKEY",
    "email": "email@email.tld",
}

valid_json = """
{
  "apikey": "APIKEY",
  "uid": "UI",
  "email": "email@email.tld"
}
"""

valid_yaml = """
apikey: APIKEY
uid: UI
email: email@email.tld
"""

invalid_json = """
{
  "apikey": "APIKEY
  "email": "email@email.tld"
}
"""

invalid_yaml = """
apikey:
  - an invalid struct:
  -
  an:
      invalid yaml
uid: UI
"""


def test_config():
    cfg = config.Config()
    assert cfg is not None


def test_set_get():
    cfg = config.Config()
    try:
        cfg["new_item"] = 42
    except Exception:
        assert "__setitem__ failed" == ""
    assert cfg["new_item"] == 42


def test_repr_str():
    cfg = config.Config()
    cfg["new_item"] = 42
    assert repr(cfg) == "{'new_item': 42}"
    assert str(cfg) == "{'new_item': 42}"


def test_validate():
    cfg = config.Config()
    cfg.cfg = valid_config
    assert cfg.validate()
    cfg.cfg = invalid_config
    assert cfg.validate() is False


def test_from_json():
    cfg = config.Config()
    _, path = tempfile.mkstemp()
    with open(path, "w") as f:
        f.write(valid_json)

    cfg.from_json(path)
    assert json.loads(valid_json) == cfg.cfg


def test_from_json_subkey():
    cfg = config.Config()
    _, path = tempfile.mkstemp()
    with open(path, "w") as f:
        f.write(valid_json)

    cfg.from_json(path, "subkey")
    assert yaml.safe_load(valid_json) == cfg["subkey"]


def test_from_json_error():
    cfg = config.Config()
    _, path = tempfile.mkstemp()

    with open(path, "w") as f:
        f.write(invalid_json)
    try:
        cfg.from_json(path)
    except JSONDecodeError:
        assert True


def test_from_yaml():
    cfg = config.Config()
    _, path = tempfile.mkstemp()
    with open(path, "w") as f:
        f.write(valid_yaml)

    cfg.from_yaml(path)
    desired = yaml.safe_load(valid_yaml)
    assert desired == cfg.cfg


def test_from_yaml_subkey():
    cfg = config.Config()
    _, path = tempfile.mkstemp()
    with open(path, "w") as f:
        f.write(valid_yaml)

    cfg.from_yaml(path, "subkey")
    assert yaml.safe_load(valid_yaml) == cfg["subkey"]


def test_from_yaml_error():
    cfg = config.Config()
    _, path = tempfile.mkstemp()

    with open(path, "w") as f:
        f.write(invalid_yaml)
    try:
        cfg.from_yaml(path)
    except yaml.YAMLError:
        assert True


def test_to_json():
    cfg = config.Config()
    _, path = tempfile.mkstemp()

    cfg.cfg = valid_config
    cfg.to_json(path)

    with open(path, "r") as f:
        assert json.load(f) == cfg.cfg


def test_to_yaml():
    cfg = config.Config()
    _, path = tempfile.mkstemp()

    cfg.cfg = valid_config
    cfg.to_yaml(path)

    with open(path, "r") as f:
        assert yaml.safe_load(f) == cfg.cfg


def test_load_and_validate():
    _, path = tempfile.mkstemp()

    with open(path, "w") as f:
        f.write(valid_yaml)

    config.config = config.Config()
    config.load_and_validate(path)

    assert "uid" in config.config
    assert config.config["uid"] == "UI"
