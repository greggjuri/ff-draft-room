"""Unit tests for utils.storage."""

from __future__ import annotations

import pytest

from utils.storage import LocalStorage, S3Storage, get_storage


# ---------------------------------------------------------------------------
# LocalStorage tests
# ---------------------------------------------------------------------------


@pytest.fixture
def local(tmp_path):
    return LocalStorage(tmp_path / "rankings")


def test_local_write_and_read(local):
    data = {"name": "Test", "players": []}
    local.write("default.json", data)
    result = local.read("default.json")
    assert result == data


def test_local_read_missing_key(local):
    assert local.read("nonexistent.json") is None


def test_local_delete(local):
    local.write("test.json", {"a": 1})
    local.delete("test.json")
    assert not local.exists("test.json")


def test_local_delete_missing(local):
    local.delete("nonexistent.json")  # should not raise


def test_local_exists_true(local):
    local.write("test.json", {"a": 1})
    assert local.exists("test.json") is True


def test_local_exists_false(local):
    assert local.exists("test.json") is False


def test_local_list_keys(local):
    local.write("a.json", {})
    local.write("b.json", {})
    keys = local.list_keys()
    assert sorted(keys) == ["a.json", "b.json"]


def test_local_list_keys_with_prefix(local):
    local.write("mock_1.json", {})
    local.write("mock_2.json", {})
    local.write("default.json", {})
    keys = local.list_keys(prefix="mock")
    assert sorted(keys) == ["mock_1.json", "mock_2.json"]


# ---------------------------------------------------------------------------
# S3Storage tests (moto)
# ---------------------------------------------------------------------------


pytest.importorskip("moto")

import boto3  # noqa: E402
from moto import mock_aws  # noqa: E402

BUCKET = "test-bucket"


@pytest.fixture
def s3():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket=BUCKET)
        storage = S3Storage(BUCKET)
        yield storage


def test_s3_write_and_read(s3):
    data = {"name": "Test", "players": []}
    s3.write("default.json", data)
    result = s3.read("default.json")
    assert result == data


def test_s3_read_missing_key(s3):
    assert s3.read("nonexistent.json") is None


def test_s3_delete(s3):
    s3.write("test.json", {"a": 1})
    s3.delete("test.json")
    assert not s3.exists("test.json")


def test_s3_exists(s3):
    assert not s3.exists("test.json")
    s3.write("test.json", {"a": 1})
    assert s3.exists("test.json")


def test_s3_list_keys(s3):
    s3.write("a.json", {})
    s3.write("b.json", {})
    keys = s3.list_keys()
    assert sorted(keys) == ["a.json", "b.json"]


# ---------------------------------------------------------------------------
# get_storage factory tests
# ---------------------------------------------------------------------------


def test_get_storage_default(tmp_path, monkeypatch):
    monkeypatch.setenv("RANKINGS_DIR", str(tmp_path / "rankings"))
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    storage = get_storage()
    assert isinstance(storage, LocalStorage)


def test_get_storage_s3_env(monkeypatch):
    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(
            Bucket="ff-draft-room-data"
        )
        monkeypatch.setenv("STORAGE_BACKEND", "s3")
        monkeypatch.setenv("S3_BUCKET", "ff-draft-room-data")
        storage = get_storage()
        assert isinstance(storage, S3Storage)
