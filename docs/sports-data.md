# Sports data and pregame features

Phase 1 uses public game data only. It does not access bet365, a wagering account, or private credentials.

## Sources and artifacts

- EPL results from 2023-24 onward come from the public football-data.co.uk season CSVs. Their historical
  Bet365 home/draw/away columns are retained as optional evaluation metadata and are never model features.
- Current EPL fixtures and statuses come from ESPN's public `eng.1` scoreboard.
- MLB regular-season schedules and results from 2024 onward come from the public MLB Stats API.

`python scripts/fetch_sports.py` fetches history and the current schedule windows. `--refresh` updates only
the previous 14 days and upcoming window, capturing recent final results while preserving earlier history. Each successful response is stored under `data/sports/raw/`
with its UTC fetch time and URL hash. `games.json` records content and URL SHA256 hashes, archive paths,
source URLs, and successful fetch times. A failed refresh reports `failed`, or `stale` when an older
successful snapshot exists; it records a separate attempt time and does not advance `fetched_at`.

The normalized game contract is:

```text
id, sport, league, start_time, home, away, home_key, away_key, status,
home_score, away_score, outcome, source, source_url, source_fetched_at, venue
```

`start_time` is a UTC ISO timestamp. `status` is one of `scheduled`, `live`, `final`, `postponed`, or
`cancelled`. Scores are null before play. Final outcomes are `0` for home, `1` for draw, and `2` for away.
MLB's optional odds field is `[null, null, null]`. Logos are included only when the source supplies them.
Stable soccer team keys map source variants such as `AFC Bournemouth`/`Bournemouth` and
`Manchester United`/`Man United` to the same identity.

## Leakage boundary and features

`build_features` sorts all observations chronologically but advances team state only at the start of a UTC
date and at least 48 hours after the prior game's scheduled start. An earlier start time, or a crossed UTC
midnight, is not evidence that its result was available before another kickoff. This conservative delay and
day-batch rule protect doubleheaders, late games, and rescheduled same-day games. Only normalized final scores
update Elo, recent form, win rate, games played, rest, and score-margin state. MLB games marked with a resume
date are retained but excluded as labels and state updates because the schedule endpoint does not provide a
trustworthy completion timestamp.
Scheduled, live, postponed, and cancelled games never update state. Provider cumulative records, current
event form, current-game scores, and results are excluded from the feature row. New teams use neutral priors.

The 16 float32 channels are:

1. `home_elo`
2. `away_elo`
3. `elo_diff`
4. `home_form`
5. `away_form`
6. `form_diff`
7. `home_win_rate`
8. `away_win_rate`
9. `home_games_played`
10. `away_games_played`
11. `home_rest_days`
12. `away_rest_days`
13. `rest_diff`
14. `home_avg_margin`
15. `away_avg_margin`
16. `is_baseball`

Elo and count-like channels are bounded/scaled for neural input. Recent form uses the last five completed
games. `dataset.npz` contains `X`, `y`, and `feature_names`; unfinished games have label `-1`.
`dataset-games.json` preserves row-to-game alignment.

The 48-hour result delay is an explicit conservative proxy rather than a sourced completion time; it can omit
information that was actually available sooner. Source availability and schedule corrections can still change
future fixtures. Historical odds are not a current offered price, and paper picks must report model
probabilities or fair model odds only.
