"""Bucket transcript tracking during plan wave parsing."""

from __future__ import annotations


class ParseBuckets:
    def __init__(self) -> None:
        self.buckets: dict[str, int] = {}
        self.transcript: list[str] = []

    def add(self, name: str) -> None:
        self.buckets[name] = self.buckets.get(name, 0) + 1
        self.transcript.append(name)
