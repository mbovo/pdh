from pdh import main
from click import testing


def test_pass():
    assert True


def test_main():
    runner = testing.CliRunner(main.main)
    assert runner
