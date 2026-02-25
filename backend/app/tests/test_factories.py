"""Tests for factory functions themselves."""

import pytest

from app.tests.factories import make_running_workout, make_strength_workout, make_workout


@pytest.mark.unit
def test_make_workout_defaults():
    workout = make_workout()
    assert workout.workout_type == "running"
    assert workout.distance_km == 10.5
    assert workout.hr_avg == 155


@pytest.mark.unit
def test_make_workout_overrides():
    workout = make_workout(distance_km=21.1, hr_avg=160)
    assert workout.distance_km == 21.1
    assert workout.hr_avg == 160


@pytest.mark.unit
def test_make_running_workout():
    workout = make_running_workout(subtype="longrun")
    assert workout.workout_type == "running"
    assert workout.subtype == "longrun"


@pytest.mark.unit
def test_make_strength_workout():
    workout = make_strength_workout()
    assert workout.workout_type == "strength"
    assert workout.subtype == "knee_dominant"
    assert workout.distance_km is None
    assert workout.pace is None
