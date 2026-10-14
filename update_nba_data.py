"""Hoops Intelligence: build per-game NBA player stats from ESPN box scores.

Uses ESPN's public scoreboard/summary endpoints (unofficial, subject to change).
Does not overwrite an existing dataset on failed or incomplete retrieval.
"""
import argparse
import csv
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
FIELDS = ['name','team','pos','pts','reb','ast','stl','blk','tov','gp','games_next_week','source','season','as_of']
STAT_KEYS = ('pts','reb','ast','stl','blk','tov')
POSITION = {'PG':'PG','SG':'SG','SF':'SF','PF':'PF','C':'C','G':'PG/SG','F':'SF/PF'}


def request_json(url, retries=3):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (compatible; HoopsIntelligence/1.0)','Accept':'application/json'})
            with urllib.request.urlopen(req, timeout=25) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            last = exc
            print(f'ESPN request failed ({attempt+1}/{retries}): {exc}', flush=True)
            if attempt + 1 < retries:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f'ESPN request failed: {url}') from last


def parse_number(value):
    try:
        return float(str(value).replace(',',''))
    except (ValueError, TypeError):
        return 0.0


def season_dates(season):
    start_year = int(season[:4])
    if season != f'{start_year}-{str(start_year+1)[-2:]}':
        raise ValueError('Season must look like 2026-27')
    return dt.date(start_year, 10, 1), dt.date(start_year+1, 4, 20)


def game_ids_for_day(day):
    params = urllib.parse.urlencode({'dates':day.strftime('%Y%m%d'),'limit':'100'})
    data = request_json(f'{BASE}/scoreboard?{params}')
    ids = []
    for event in data.get('events', []):
        status = event.get('status', {}).get('type', {})
        if status.get('completed') is True:
            ids.append(str(event['id']))
    return ids


def parse_box_score(game_id):
    data = request_json(f'{BASE}/summary?event={urllib.parse.quote(game_id)}')
    box = data.get('boxscore', {})
    out = []
    for team_block in box.get('players', []):
        team = team_block.get('team', {}).get('abbreviation', 'UNK')
        for group in team_block.get('statistics', []):
            labels = [str(x).upper() for x in group.get('labels', [])]
            if not {'PTS','REB','AST','STL','BLK','TO'}.issubset(set(labels)):
                continue
            for item in group.get('athletes', []):
                athlete = item.get('athlete', {})
                values = item.get('stats', [])
                if len(values) != len(labels) or item.get('didNotPlay') is True:
                    continue
                d = dict(zip(labels, values))
                mins = str(d.get('MIN', '')).strip()
                if mins in ('', '--', '0', '0:00'):
                    continue
                athlete_id = str(athlete.get('id', '')).strip()
                name = str(athlete.get('displayName', '')).strip()
                if not athlete_id or not name:
                    continue
                position = athlete.get('position', {}) or {}
                pos = str(position.get('abbreviation', 'N/A')).upper()
                out.append({'id':athlete_id,'name':name,'team':team,'pos':POSITION.get(pos,pos),
                            **{key:parse_number(d[label]) for key,label in [('pts','PTS'),('reb','REB'),('ast','AST'),('stl','STL'),('blk','BLK'),('tov','TO')]}})
    if len(out) < 10:
        raise ValueError(f'Game {game_id} has only {len(out)} player rows; box score may be incomplete')
    return out


def build(season, start, end, min_players, min_games):
    totals = {}
    games = 0
    day = start
    while day <= end:
        ids = game_ids_for_day(day)
        print(f'{day}: {len(ids)} completed games', flush=True)
        for game_id in ids:
            entries = parse_box_score(game_id)
            seen = set()
            for player in entries:
                pid = player['id']
                if pid in seen:
                    continue
                seen.add(pid)
                if pid not in totals:
                    totals[pid] = {'name':player['name'],'team':player['team'],'pos':player['pos'],
                                   'gp':0, **{k:0.0 for k in STAT_KEYS}}
                agg = totals[pid]
                agg['name'],agg['team'] = player['name'],player['team']
                if player['pos'] not in ('N/A',''):
                    agg['pos'] = player['pos']
                agg['gp'] += 1
                for k in STAT_KEYS:
                    agg[k] += player[k]
            games += 1
            time.sleep(0.15)
        day += dt.timedelta(days=1)
    if games < min_games or len(totals) < min_players:
        raise RuntimeError(f'Incomplete extraction: {games} games, {len(totals)} players. '
                           f'Minimum required: {min_games} games and {min_players} players. Existing CSV unchanged.')
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    rows = []
    for p in totals.values():
        gp = p['gp']
        rows.append({'name':p['name'],'team':p['team'],'pos':p['pos'],
                     **{k:round(p[k]/gp,3) for k in STAT_KEYS},'gp':gp,
                     'games_next_week':'','source':'ESPN NBA box scores (unofficial API)',
                     'season':season,'as_of':now})
    return sorted(rows, key=lambda p:p['name'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--season', default='2026-27')
    parser.add_argument('--output', default=str(Path(__file__).with_name('players.csv')))
    parser.add_argument('--start', help='YYYY-MM-DD, optional narrower backfill window')
    parser.add_argument('--end', help='YYYY-MM-DD, optional narrower backfill window')
    parser.add_argument('--min-players', type=int, default=100)
    parser.add_argument('--min-games', type=int, default=10)
    args = parser.parse_args()
    first,last = season_dates(args.season)
    today = dt.datetime.now(dt.timezone.utc).date()
    start = dt.date.fromisoformat(args.start) if args.start else first
    end = dt.date.fromisoformat(args.end) if args.end else min(last,today)
    if start < first or end > last or start > end:
        raise ValueError('Date range outside season or inverted')
    rows = build(args.season,start,end,args.min_players,args.min_games)
    output = Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    temp = output.with_suffix(output.suffix+'.tmp')
    try:
        with temp.open('w',encoding='utf-8',newline='') as file:
            writer = csv.DictWriter(file,fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp,output)
    finally:
        if temp.exists():
            temp.unlink()
    print(f'SUCCESS: {len(rows)} players -> {output}',flush=True)

if __name__ == '__main__':
    main()
