
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)


# Keep an original snapshot so tests can restore the in-memory DB
_ORIGINAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def restore_activities():
    # restore activities before each test to ensure isolation
    activities.clear()
    activities.update(deepcopy(_ORIGINAL_ACTIVITIES))
    yield


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # Basic sanity checks
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_unregistration_flow():
    activity = "Basketball Team"
    email = "teststudent@example.com"

    # ensure not in participants initially
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]

    # signup
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json()["message"]

    # verify present
    resp = client.get("/activities")
    assert email in resp.json()[activity]["participants"]

    # unregister
    resp = client.delete(f"/activities/{activity}/participants?email={email}")
    assert resp.status_code == 200
    assert "Unregistered" in resp.json()["message"]

    # verify removed
    resp = client.get("/activities")
    assert email not in resp.json()[activity]["participants"]


def test_signup_duplicate():
    activity = "Chess Club"
    email = "duplicate@example.com"

    # first signup should succeed
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200

    # second signup should fail with 400
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 400


def test_unregister_nonexistent():
    activity = "Tennis Club"
    email = "notfound@example.com"
    resp = client.delete(f"/activities/{activity}/participants?email={email}")
    assert resp.status_code == 404
