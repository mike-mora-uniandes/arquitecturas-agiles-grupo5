import pytest

from locustfile import SCENARIO_PLAN, pick_scenario


def test_scenario_plan_has_recommended_matrix():
    required = {"E0", "E1", "E2", "E3"}
    assert required.issubset(SCENARIO_PLAN)

    for name, scenario in SCENARIO_PLAN.items():
        customer_id = scenario["customer_id"]
        assert scenario["open_data"].endswith(f"/{customer_id}")
        assert scenario["open_finance"].endswith(f"/{customer_id}")
        assert scenario["expected_asrs"]


def test_pick_scenario_returns_valid_scenario_name():
    assert pick_scenario() in SCENARIO_PLAN
