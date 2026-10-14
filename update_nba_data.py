"""Optional public NBA stats importer. Requires: pip install nba_api
Run: python update_nba_data.py --season 2025-26
Fetch can fail due to NBA.com rate limits or access controls. No fabricated fallback.
"""
import argparse
import csv
import datetime as dt
from pathlib import Path

FIELDS = ['name','team','pos','pts','reb','ast','stl','blk','tov','gp','games_next_week','source','season','as_of']

def transform(rows, season, as_of):
    output=[]
    for row in rows:
        name=str(row.get('PLAYER_NAME','')).strip()
        if not name: continue
        gp=int(row['GP'])
        if gp < 1: continue
        output.append(dict(name=name,team=str(row.get('TEAM_ABBREVIATION','UNK')),
          pos='N/A',pts=float(row['PTS']),reb=float(row['REB']),ast=float(row['AST']),
          stl=float(row['STL']),blk=float(row['BLK']),tov=float(row['TOV']),
          gp=gp,games_next_week='',source='NBA.com stats via nba_api (unofficial)',
          season=season,as_of=as_of))
    if not output: raise ValueError('No player rows returned; refusing to replace dataset')
    return output

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--season',default='2025-26')
    ap.add_argument('--output',default=str(Path(__file__).parent/'players.csv'))
    args=ap.parse_args()
    from nba_api.stats.endpoints import leaguedashplayerstats
    result=leaguedashplayerstats.LeagueDashPlayerStats(season=args.season,per_mode_detailed='PerGame',timeout=30)
    data=result.get_normalized_dict()['LeagueDashPlayerStats']
    records=transform(data,args.season,dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    output=Path(args.output)
    temp=output.with_suffix('.tmp')
    with temp.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(records)
    temp.replace(output)
    print(f'Updated {output} with {len(records)} NBA player rows. Positions not supplied; marked N/A.')

if __name__=='__main__':main()
