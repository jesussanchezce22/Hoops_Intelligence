"""Offline validation of the NBA stats transformation; no fabricated live dataset."""
import csv
import tempfile
import unittest
from pathlib import Path
from update_nba_data import transform, FIELDS

class DataPipelineTests(unittest.TestCase):
    def test_per_game_mapping_and_metadata(self):
        sample = [{'PLAYER_NAME':'Example Player','TEAM_ABBREVIATION':'ABC','GP':42,
                   'PTS':21.5,'REB':7.2,'AST':6.1,'STL':1.3,'BLK':0.6,'TOV':2.7}]
        rows=transform(sample,'2025-26','2026-10-12T00:00:00Z')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['pts'],21.5)
        self.assertEqual(rows[0]['gp'],42)
        self.assertEqual(rows[0]['pos'],'N/A')
        self.assertEqual(rows[0]['season'],'2025-26')
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'players.csv'
            with p.open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=FIELDS)
                writer.writeheader();writer.writerows(rows)
            with p.open(newline='',encoding='utf-8') as f:
                imported=list(csv.DictReader(f))
            self.assertEqual(imported[0]['name'],'Example Player')
            self.assertEqual(imported[0]['pts'],'21.5')

    def test_empty_data_does_not_publish(self):
        with self.assertRaisesRegex(ValueError,'No player rows'):
            transform([], '2025-26', '2026-10-12T00:00:00Z')

    def test_zero_games_filtered(self):
        sample=[{'PLAYER_NAME':'Example Player','GP':0}]
        with self.assertRaises(ValueError):
            transform(sample,'2025-26','2026-10-12T00:00:00Z')

if __name__=='__main__': unittest.main()
