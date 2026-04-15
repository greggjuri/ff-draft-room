"""Storage backend abstraction for rankings data."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class StorageBackend(ABC):
    """Abstract base for rankings data persistence."""

    @abstractmethod
    def read(self, key: str) -> dict[str, Any] | None: ...

    @abstractmethod
    def write(self, key: str, data: dict[str, Any]) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def list_keys(self, prefix: str = "") -> list[str]: ...


class LocalStorage(StorageBackend):
    """Filesystem storage. Used in local dev and all tests."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        base_dir.mkdir(parents=True, exist_ok=True)

    def read(self, key: str) -> dict[str, Any] | None:
        path = self.base_dir / key
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def write(self, key: str, data: dict[str, Any]) -> None:
        (self.base_dir / key).write_text(json.dumps(data, indent=2))

    def delete(self, key: str) -> None:
        path = self.base_dir / key
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return (self.base_dir / key).exists()

    def list_keys(self, prefix: str = "") -> list[str]:
        return sorted(
            p.name for p in self.base_dir.glob(f"{prefix}*.json")
        )


class S3Storage(StorageBackend):
    """Production S3 backend. Auth via EC2 IAM instance role."""

    def __init__(self, bucket: str, prefix: str = "rankings/"):
        import boto3

        self.client = boto3.client("s3")
        self.bucket = bucket
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def read(self, key: str) -> dict[str, Any] | None:
        try:
            obj = self.client.get_object(
                Bucket=self.bucket, Key=self._key(key)
            )
            return json.loads(obj["Body"].read())
        except self.client.exceptions.NoSuchKey:
            return None

    def write(self, key: str, data: dict[str, Any]) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=self._key(key),
            Body=json.dumps(data, indent=2),
            ContentType="application/json",
        )

    def delete(self, key: str) -> None:
        self.client.delete_object(
            Bucket=self.bucket, Key=self._key(key)
        )

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(
                Bucket=self.bucket, Key=self._key(key)
            )
            return True
        except self.client.exceptions.ClientError:
            return False

    def list_keys(self, prefix: str = "") -> list[str]:
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=f"{self.prefix}{prefix}",
        )
        full_prefix = self.prefix
        return [
            obj["Key"].removeprefix(full_prefix)
            for obj in response.get("Contents", [])
        ]


def get_storage() -> StorageBackend:
    """Factory. Reads STORAGE_BACKEND env var. Default: local."""
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    if backend == "s3":
        bucket = os.environ["S3_BUCKET"]
        return S3Storage(bucket)
    base_dir = Path(os.getenv("RANKINGS_DIR", "data/rankings"))
    return LocalStorage(base_dir)
