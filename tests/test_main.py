from pdh import main
from click import testing
import pkg_resources


def test_assert_true():
    assert True


def test_main_cli():
    runner = testing.CliRunner()
    assert runner.invoke(main.main, "").exit_code == 0


def test_main_version():
    runner = testing.CliRunner()
    result = runner.invoke(main.main, "version")
    assert result.exit_code == 0
    assert result.stdout == f"v{pkg_resources.get_distribution('pdh').version}\n"
