"""Valida invariantes da entrega sem iniciar APIs ou interfaces."""
import json
import hashlib
import pickle
import unittest
from pathlib import Path

from source.experiment import BASE, evaluate, predict_bundle


class DeliveryTests(unittest.TestCase):
    def test_artifact_manifest_is_current(self):
        manifest = json.loads((BASE/"results/manifest.json").read_text())
        for name, item in manifest["files"].items():
            data = (BASE/name).read_bytes()
            self.assertEqual(len(data), item["bytes"], name)
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"], name)

    def test_requested_plk_is_identical_to_pickle(self):
        self.assertEqual((BASE/"models/modelo_treinado.pkl").read_bytes(), (BASE/"models/modelo_treinado.plk").read_bytes())

    def test_zero_accepted_has_no_perfect_accuracy(self):
        metrics = evaluate([0, 1], [.51, .49], threshold=.99)
        self.assertEqual(metrics['accepted_count'], 0)
        self.assertIsNone(metrics['accepted_accuracy'])
        self.assertIsNone(metrics['accepted_error'])

    def test_saved_split_groups_and_texts_do_not_leak(self):
        rows = [json.loads(line) for line in (BASE/'results/splits.jsonl').read_text().splitlines()]
        groups, hashes, ids = {}, {}, set()
        for row in rows:
            self.assertNotIn(row['id'], ids)
            ids.add(row['id'])
            if row['group'] in groups:
                self.assertEqual(groups[row['group']], row['split'])
            groups[row['group']] = row['split']
            self.assertNotIn(row['text_sha256'], hashes)
            hashes[row['text_sha256']] = row['split']
        self.assertEqual(len(rows), 7199)

    def test_exported_model_abstains_outside_vocabulary(self):
        with (BASE/'models/modelo_treinado.pkl').open('rb') as file:
            model = pickle.load(file)
        result = predict_bundle(model, ['xqzv ttrn wpxk lzzq vvvx rrqq'])[0]
        self.assertEqual(result['label'], 'abstain')
        self.assertEqual(result['abstention_reason'], 'outside_vocabulary')

    def test_reported_accuracy_agrees_with_individual_predictions(self):
        rows = [json.loads(line) for line in (BASE/'results/test_predictions.jsonl').read_text().splitlines()]
        metrics = json.loads((BASE/'results/metrics.json').read_text())['calibrated_test']
        self.assertEqual(len(rows), metrics['n'])
        self.assertAlmostEqual(sum(row['correct'] for row in rows)/len(rows), metrics['accuracy'], places=12)


if __name__ == '__main__':
    unittest.main()
