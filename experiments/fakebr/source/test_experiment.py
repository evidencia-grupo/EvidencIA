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

    def test_reproduction_matches_received_delivery(self):
        """Baseline de proveniência: a reprodução concorda com a entrega recebida (tolerância 1e-10)."""
        def leaves(node, path=""):
            if isinstance(node, dict):
                for key, value in node.items():
                    yield from leaves(value, f"{path}/{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    yield from leaves(value, f"{path}[{index}]")
            else:
                yield path, node

        # Tempo de parede e plataforma descrevem a máquina, não o resultado científico.
        volatile = ('/training_and_evaluation_seconds', '/environment/')
        current = {k: v for k, v in leaves(json.loads((BASE/'results/metrics.json').read_text())) if not k.startswith(volatile)}
        received = {k: v for k, v in leaves(json.loads((BASE/'results/metrics_recebidas.json').read_text())) if not k.startswith(volatile)}
        self.assertEqual(current.keys(), received.keys())
        for key, value in current.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self.assertAlmostEqual(value, received[key], delta=1e-10, msg=key)
            else:
                self.assertEqual(value, received[key], key)

        received_manifest = json.loads((BASE/'results/manifest_recebido.json').read_text())
        for name in ('results/splits.jsonl', 'results/test_predictions.jsonl'):
            self.assertEqual(hashlib.sha256((BASE/name).read_bytes()).hexdigest(), received_manifest['files'][name]['sha256'], name)

    def test_reported_accuracy_agrees_with_individual_predictions(self):
        rows = [json.loads(line) for line in (BASE/'results/test_predictions.jsonl').read_text().splitlines()]
        metrics = json.loads((BASE/'results/metrics.json').read_text())['calibrated_test']
        self.assertEqual(len(rows), metrics['n'])
        self.assertAlmostEqual(sum(row['correct'] for row in rows)/len(rows), metrics['accuracy'], places=12)


if __name__ == '__main__':
    unittest.main()
