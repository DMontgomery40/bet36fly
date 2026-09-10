from concurrent.futures import ThreadPoolExecutor
import csv
import io
import pytest

from bet36fly.ledger import PickLedger, fixture_identity


def record(n=1):
    return {'game_id': f'g{n}', 'run_id': 'r1', 'feature_hash': 'features1', 'model_hash': 'sha',
            'sport': 'soccer', 'home': 'Home', 'away': 'Away', 'start_time': '2026-09-20T12:00:00Z',
            'created_at': '2026-09-10T12:00:00Z', 'pick': 'home', 'pick_label': 'Home',
            'probabilities': {'home': .5, 'draw': .2, 'away': .3}, 'confidence': .5, 'fair_odds': 2.,
            'source_url': 'https://example.com/game', 'source_fetched_at': '2026-09-10T12:00:00Z'}


def test_paper_ledger_is_durable_idempotent_and_revision_aware(tmp_path):
    ledger = PickLedger(tmp_path / 'ledger.sqlite3')
    a = ledger.add(record())
    b = ledger.add(record())
    assert a['id'] == b['id']
    assert a['mode'] == 'paper' and a['status'] == 'proposed'
    changed = record()
    changed['feature_hash'] = 'new_features'
    ledger.add(changed)
    assert len(PickLedger(tmp_path / 'ledger.sqlite3').all()) == 2


def test_concurrent_inference_does_not_duplicate_pick(tmp_path):
    ledger = PickLedger(tmp_path / 'ledger.sqlite3')
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(lambda _: ledger.add(record())['id'], range(12)))
    assert len(set(ids)) == 1
    assert len(ledger.all()) == 1


def test_csv_exports_all_rows_and_escapes_spreadsheet_formulas(tmp_path):
    ledger = PickLedger(tmp_path / 'ledger.sqlite3')
    row = record()
    row['home'] = '=HYPERLINK("unsafe")'
    ledger.add(row)
    ledger.add(record(2))
    csv = ledger.export_csv()
    assert len(csv.splitlines()) == 3
    assert "'=HYPERLINK" in csv


@pytest.mark.parametrize('change, expected_rows', [
    ({'source_fetched_at': '2026-09-11T00:00:00Z'}, 1),
    ({'start_time': '2026-09-20T14:00:00+02:00'}, 1),
    ({'start_time': '2026-09-20T20:00:00Z'}, 2),
    ({'start_time': '2026-09-21T12:00:00Z'}, 2),
    ({'home': 'Corrected team'}, 2),
    ({'away': 'Corrected opponent'}, 2),
    ({'sport': 'baseball'}, 2),
    ({'feature_hash': 'new_features'}, 2),
])
def test_fixture_revisions_preserve_history_and_unchanged_refreshes_reuse(tmp_path, change, expected_rows):
    ledger = PickLedger(tmp_path / 'ledger.sqlite3')
    original = ledger.add(record())
    revised = dict(record(), **change)
    revised['created_at'] = '2026-09-11T01:00:00Z'
    current = ledger.add(revised)
    assert (original['id'] == current['id']) == (expected_rows == 1)
    assert current['fixture_hash'] == fixture_identity(revised)
    assert ledger.latest('r1')['g1']['id'] == current['id']
    rows = list(csv.DictReader(io.StringIO(ledger.export_csv())))
    assert len(rows) == expected_rows
    if expected_rows == 2:
        assert current['start_time'] == revised['start_time']
        assert any(row['start_time'] == original['start_time'] for row in rows)
