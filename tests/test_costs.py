import pytest

from gateway_ranker.evaluation import episode_cost


def test_fault_cost_includes_the_visit_week() -> None:
    assert episode_cost(episode_weeks=4, first_visit_week=2) == 1_580


def test_unvisited_fault_is_charged_for_the_whole_episode() -> None:
    assert episode_cost(episode_weeks=4) == 2_400


def test_visit_week_must_be_inside_the_episode() -> None:
    with pytest.raises(ValueError, match="inside the episode"):
        episode_cost(episode_weeks=4, first_visit_week=5)
