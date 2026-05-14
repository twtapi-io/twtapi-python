"""Shared fixtures.

Tests never hit production — every HTTP call is mocked with `respx`.
"""

from __future__ import annotations

import pytest

from twtapi import TwtAPI, TwtAPIAsync


@pytest.fixture
def client() -> TwtAPI:
    return TwtAPI(api_key="tw_test_key", retries=0)


@pytest.fixture
def async_client() -> TwtAPIAsync:
    return TwtAPIAsync(api_key="tw_test_key", retries=0)
