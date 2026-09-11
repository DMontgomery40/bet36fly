from datetime import datetime, timedelta, timezone
import numpy as np
import pytest
from bet36fly.shadow import ShadowLedger, ensemble_probability, model_identity

NOW = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)


def pointer():
    return dict(experiment_id='v2-test', variant='bio-shared-temporal', bundles=[{'seed': s} for s in (42, 137, 2026)],
                baseline_sha256='baseline', activated_at=(NOW - timedelta(hours=1)).isoformat())


@pytest.mark.parametrize('tamper', [None, 'bundle', 'baseline'])
def test_shadow_loads_json_path_strings_and_checks_hashes(tmp_path, monkeypatch, tamper):
    from bet36fly import experiment_v2
    from bet36fly.connectome import digest
    from bet36fly.experiment import atomic_json
    from bet36fly.shadow import ShadowRuntime
    output = tmp_path / 'output'
    output.mkdir()
    bundle, baseline = output / 'bundle.json', output / 'baseline.json'
    atomic_json(bundle, {'candidate': True})
    atomic_json(baseline, {'models': {}})
    frozen = dict(pointer(), bundles=[dict(path=str(bundle), sha256=digest(bundle), seed=s)
                                     for s in (42, 137, 2026)],
                  baseline_path=str(baseline), baseline_sha256=digest(baseline))
    atomic_json(output / 'v2-shadow.json', frozen)
    loaded = []
    monkeypatch.setattr(experiment_v2, 'load_candidate', lambda path: loaded.append(path) or object())
    runtime = ShadowRuntime(tmp_path)
    if tamper:
        (bundle if tamper == 'bundle' else baseline).write_text('{}')
        with pytest.raises(ValueError, match=f'Shadow {tamper} identity changed'):
            runtime.ensure()
        assert not loaded and runtime.pointer is None
    else:
        assert runtime.ensure() and len(runtime.candidates) == 3
        assert runtime.ensure() and len(loaded) == 3


def game(index=0, sport='soccer'):
    return dict(id=str(index), sport=sport, home='A', away='B', status='scheduled',
                start_time=(NOW + timedelta(hours=2)).isoformat(), source_fetched_at=NOW.isoformat())


def capture(ledger, fixture, **kwargs):
    return ledger.capture(fixture, np.zeros(16), pointer=kwargs.pop('pointer', pointer()),
        predict=kwargs.pop('predict', lambda x: [[.6, 0, .4]] * 3), baseline_predict=lambda x: [.5, 0, .5],
        current_fixture=kwargs.pop('current_fixture', lambda gid: fixture),
        clock=kwargs.pop('clock', lambda: NOW), **kwargs)


def test_first_forecast_is_idempotent_per_revision_and_model(tmp_path):
    ledger = ShadowLedger(tmp_path / 'shadow.db')
    original = game()
    first = capture(ledger, original)
    assert capture(ledger, original, predict=lambda x: pytest.fail('must reuse first forecast')) == first
    revised = dict(original, start_time=(NOW + timedelta(days=1)).isoformat())
    second = capture(ledger, revised)
    third = capture(ledger, original, pointer=dict(pointer(), baseline_sha256='new-model'))
    assert len({first['id'], second['id'], third['id']}) == 3
    assert len(ledger.forecasts()) == 3
    # Re-fetch timestamps and changed feature values do not replace the first valid forecast.
    assert capture(ledger, dict(original, source_fetched_at=(NOW - timedelta(minutes=1)).isoformat())) == first


@pytest.mark.parametrize('change', ['starts', 'revised', 'cancelled', 'missing', 'actual_start', 'future_source'])
def test_cutoff_race_revision_and_source_time_rejection(tmp_path, change):
    ledger = ShadowLedger(tmp_path / 'shadow.db')
    original = game()
    latest = dict(original)
    if change == 'starts':
        times = iter([NOW, NOW + timedelta(hours=2)])
        assert capture(ledger, original, clock=lambda: next(times)) is None
        return
    if change == 'revised':
        latest['start_time'] = (NOW + timedelta(days=1)).isoformat()
    elif change == 'cancelled':
        latest['status'] = 'cancelled'
    elif change == 'missing':
        latest = None
    elif change == 'actual_start':
        latest['actual_start_time'] = NOW.isoformat()
    elif change == 'future_source':
        original['source_fetched_at'] = (NOW + timedelta(minutes=1)).isoformat()
    assert capture(ledger, original, current_fixture=lambda gid: latest) is None
    assert ledger.forecasts() == []


def test_conservative_results_voids_duplicate_scores_and_exact_cohort_freeze(tmp_path):
    ledger = ShadowLedger(tmp_path / 'shadow.db')
    fixtures = [game(i) for i in range(4)]
    for fixture in fixtures:
        capture(ledger, fixture)
    future = NOW + timedelta(hours=4)
    finals = [dict(g, status='final', home_score=2, away_score=0, outcome=0,
                   source_fetched_at=future.isoformat()) for g in fixtures]
    model = model_identity(pointer())
    thresholds = {'soccer': 2, 'baseball': 3}
    first = ledger.score(finals[:1], model=model, now=future, thresholds=thresholds)
    assert first['sports']['soccer']['status'] == 'pending'
    second = ledger.score(finals[:3], model=model, now=future, thresholds=thresholds)
    cohort = second['sports']['soccer']
    assert cohort['status'] == 'frozen' and len(cohort['cohort_ids']) == 2
    assert cohort['metrics']['shadow']['n'] == 2
    for _ in range(2):
        status = ledger.score(finals, model=model, now=future, thresholds=thresholds)
        assert status['sports']['soccer']['cohort_ids'] == cohort['cohort_ids']
        assert status['sports']['soccer']['metrics'] == cohort['metrics']
    finals[0]['status'] = 'cancelled'
    status = ledger.score(finals, model=model, now=future, thresholds=thresholds)
    assert status['sports']['soccer']['void'] == 1
    assert status['sports']['baseball']['metrics'] is None


def test_ensemble_probability_arithmetic_and_invalid_vectors():
    values = [[.2, .1, .7], [.6, .2, .2], [.7, 0, .3]]
    np.testing.assert_allclose(ensemble_probability(values), [.5, .1, .4])
    for invalid in (values[:2], [[1, 1, 1]] * 3, [[float('nan'), 0, 1]] * 3):
        with pytest.raises(ValueError):
            ensemble_probability(invalid)


def test_late_actual_start_and_inconsistent_final_are_not_scored(tmp_path):
    ledger = ShadowLedger(tmp_path / 'shadow.db')
    fixture = game()
    capture(ledger, fixture)
    future = NOW + timedelta(hours=4)
    final = dict(fixture, status='final', home_score=2, away_score=0, outcome=2,
                 source_fetched_at=future.isoformat())
    model = model_identity(pointer())
    assert ledger.score([final], model=model, now=future)['sports']['soccer']['eligible_completed'] == 0
    final.update(outcome=0, actual_start_time=(NOW - timedelta(minutes=1)).isoformat())
    assert ledger.score([final], model=model, now=future)['sports']['soccer']['eligible_completed'] == 0


@pytest.mark.parametrize('disqualify', ['cancelled', 'actual_start', 'revision', 'inconsistent'])
def test_frozen_membership_never_keeps_invalid_results_in_metrics(tmp_path, disqualify):
    ledger = ShadowLedger(tmp_path / 'shadow.db')
    fixtures = [game(i) for i in range(3)]
    saved = [capture(ledger, fixture) for fixture in fixtures]
    future = NOW + timedelta(hours=4)
    finals = [dict(g, status='final', home_score=2, away_score=0, outcome=0,
                   source_fetched_at=future.isoformat()) for g in fixtures]
    model, thresholds = model_identity(pointer()), {'soccer': 2, 'baseball': 3}
    before = ledger.score(finals[:2], model=model, now=future, thresholds=thresholds)['sports']['soccer']
    assert set(before['cohort_ids']) == {r['id'] for r in saved[:2]}
    if disqualify == 'cancelled':
        finals[0]['status'] = 'cancelled'
    elif disqualify == 'actual_start':
        finals[0]['actual_start_time'] = NOW.isoformat()
    elif disqualify == 'revision':
        finals[0]['start_time'] = (NOW + timedelta(hours=1)).isoformat()
    else:
        finals[0]['outcome'] = 2
    after = ledger.score(finals, model=model, now=future, thresholds=thresholds)['sports']['soccer']
    assert after['cohort_ids'] == before['cohort_ids']
    assert after['cohort_eligible'] == 1 and after['cohort_invalidated'] == 1
    assert after['metrics']['shadow']['n'] == 1


def test_first_completed_observation_survives_refresh_and_defines_cohort_order(tmp_path):
    ledger = ShadowLedger(tmp_path / 'shadow.db')
    fixtures = [game(i) for i in range(3)]
    saved = [capture(ledger, fixture) for fixture in fixtures]
    first_time, second_time = NOW + timedelta(hours=4), NOW + timedelta(hours=5)
    first = dict(fixtures[1], status='final', home_score=2, away_score=0, outcome=0,
                 source_fetched_at=first_time.isoformat())
    model, thresholds = model_identity(pointer()), {'soccer': 2, 'baseball': 3}
    ledger.score([fixtures[0], first, fixtures[2]], model=model, now=first_time, thresholds=thresholds)
    finals = [dict(g, status='final', home_score=2, away_score=0, outcome=0,
                   source_fetched_at=second_time.isoformat()) for g in fixtures]
    status = ledger.score(finals, model=model, now=second_time, thresholds=thresholds)['sports']['soccer']
    assert status['cohort_ids'][0] == saved[1]['id']
    assert len(status['cohort_ids']) == 2
    with ledger.connect() as db:
        import json
        current = json.loads(db.execute('SELECT payload FROM scores WHERE id=?', (saved[1]['id'],)).fetchone()[0])
    assert current['first_completed_at'] == first_time.isoformat()
    assert current['observed_at'] == second_time.isoformat()
