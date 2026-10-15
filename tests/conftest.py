import pytest

from fixtures.build import build_all


@pytest.fixture(scope="session")
def _built(tmp_path_factory):
    return build_all(tmp_path_factory.mktemp("fx"))


@pytest.fixture(scope="session")
def fx(_built):
    return _built[0]


@pytest.fixture(scope="session")
def pkis(_built):
    return _built[1]


@pytest.fixture(autouse=True)
def _isolated_config(monkeypatch, tmp_path):
    monkeypatch.setenv("WMD_CONFIG", str(tmp_path / "no-such-config.toml"))
