from unittest.mock import Mock

import pytest

from bet36fly.server import follow_sources


def test_startup_and_next_cycle_refresh_with_a_bounded_stop():
    runtime, stop = Mock(), Mock()
    stop.is_set.return_value = False
    stop.wait.side_effect = [False, True]
    follow_sources(runtime, stop)
    assert runtime.warm_picks.call_count == runtime.refresh.call_count == 2
    assert [call.args for call in stop.wait.call_args_list] == [(900,), (900,)]


@pytest.mark.parametrize('unready', [False, RuntimeError('Checkpoint temporarily unavailable')])
def test_unready_or_failed_model_retries_then_recovers(unready):
    runtime, stop = Mock(), Mock()
    runtime.ensure_model.side_effect = [unready, True]
    stop.is_set.side_effect = [False, False]
    stop.wait.side_effect = [False, True]
    follow_sources(runtime, stop)
    assert runtime.refresh.call_count == runtime.warm_picks.call_count == 1
    assert [call.args for call in stop.wait.call_args_list] == [(10,), (900,)]
    if isinstance(unready, Exception):
        assert runtime.refresh_state['status'] == 'failed'


def test_stopped_server_does_not_start_another_cycle():
    runtime, stop = Mock(), Mock()
    stop.is_set.return_value = True
    follow_sources(runtime, stop)
    runtime.ensure_model.assert_not_called()
