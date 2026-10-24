"""Canonical career selection and evidence-limited mapping API regressions."""
import unittest

from fastapi.testclient import TestClient
from main import app
from reskilling.sdg_alignment import get_sdg_alignment, get_sdg_careers


class SDGCareerTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def search(self, query):
        response = self.client.get('/api/sdg/careers', params={'q': query})
        self.assertEqual(response.status_code, 200)
        return response.json()['results']

    def test_environmental_aliases_use_canonical_occupational_id(self):
        for title in ('Environmental Engineer', 'environmental engineer',
                      '  ENVIRONMENTAL   ENGINEERS  '):
            with self.subTest(title=title):
                results = self.search(title)
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]['id'], '17-2081.00')
                self.assertEqual(results[0]['title'], 'Environmental Engineers')
                self.assertEqual(results[0]['kind'], 'occupation')
                self.assertEqual(results[0]['mapping_availability'], 'suggested')
                self.assertEqual(results[0]['matched_by'], 'exact')

    def test_prototype_identity_is_not_an_occupational_record(self):
        result = self.search('  DATA   ANALYST  ')[0]
        self.assertEqual(result['id'], 'prototype:data-analyst')
        self.assertEqual(result['kind'], 'prototype')
        self.assertEqual(result['title'], 'Data Analyst')
        data = self.client.post('/api/sdg/mindmap', json={'career_id': result['id']}).json()
        self.assertEqual(data['career_id'], result['id'])
        self.assertEqual(data['status'], 'curated')
        self.assertEqual([item['target_id'] for item in data['mappings'] if item['target_id']], ['4.4', '8.5'])
        self.assertIn(9, [item['sdg_id'] for item in data['mappings']])
        self.assertTrue(all(item['career_id'] == result['id'] for item in data['mappings']))
        self.assertTrue(all(item['review_status'] == 'curated_illustrative' for item in data['mappings'] if item['target_id']))
        for mapping in data['mappings']:
            self.assertTrue(mapping['supporting_evidence'])
            if mapping['target_id']:
                self.assertIn('Illustrative pathway requirement: SQL', mapping['supporting_evidence'][0])
            self.assertEqual(set(mapping['supporting_source_ids']),
                             {source['id'] for source in mapping['evidence_source']})
            self.assertTrue(all(source['url'] and source['scope'] for source in mapping['evidence_source']))
            # Existing curated target links use different evidence-limitation
            # wording from the new rule-based occupational suggestions.
            limitations = mapping['impact_limitations'].lower()
            if mapping['review_status'] == 'curated_illustrative':
                self.assertIn('measurable progress', limitations)
                self.assertIn('not independently validated', limitations)
            else:
                self.assertIn('impact', limitations)
                self.assertIn('no un target', limitations)
                self.assertIn('measured impact', limitations)

    def test_existing_occupational_alias_mappings_are_preserved(self):
        for title, career_id in (
            ('Software Developer', '15-1252.00'),
            ('Information Security Analysts', '15-1212.00'),
            ('Web and Digital Interface Designers', '15-1255.00'),
        ):
            with self.subTest(title=title):
                result = self.search(title)[0]
                self.assertEqual(result['id'], career_id)
                data = self.client.post('/api/sdg/mindmap', json={'career_id': career_id}).json()
                self.assertEqual(data['status'], 'curated')
                self.assertEqual({item['target_id'] for item in data['mappings'] if item['target_id']}, {'4.4', '8.5'})

    def test_environmental_engineers_receive_distinct_thematic_suggestions(self):
        response = self.client.post('/api/sdg/mindmap', json={'career_id': '17-2081.00'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['career'], 'Environmental Engineers')
        self.assertEqual(data['status'], 'suggested')
        self.assertEqual({m['sdg_id'] for m in data['mappings']}, {6, 9, 13})
        self.assertTrue(all(m['target_id'] is None for m in data['mappings']))
        self.assertTrue(all(m['review_status'] == 'rule_based_suggestion' for m in data['mappings']))
        self.assertEqual(data['pathway_skills'], [])
        self.assertIn('not reviewed', data['evidence_scope'])

    def test_every_one_of_923_occupations_has_distinctly_labeled_goal_suggestions(self):
        occupations = {
            career_id: record for career_id, record in get_sdg_careers().items()
            if record["kind"] == "occupation"
        }
        self.assertEqual(len(occupations), 923)
        observed_goals = set()
        for career_id in occupations:
            data = self.client.post('/api/sdg/mindmap', json={'career_id': career_id}).json()
            self.assertIn(data['status'], ('curated', 'suggested'))
            self.assertTrue(data['mappings'], career_id)
            goal_ids = [m['sdg_id'] for m in data['mappings']]
            self.assertEqual(len(goal_ids), len(set(goal_ids)), career_id)
            self.assertTrue(all(1 <= goal <= 17 for goal in goal_ids))
            self.assertTrue(all(m['career_id'] == career_id for m in data['mappings']))
            for m in data['mappings']:
                if m['review_status'] == 'rule_based_suggestion':
                    self.assertIsNone(m['target_id'])
                    self.assertEqual(m['mapping_kind'], 'occupation_theme')
            observed_goals.update(goal_ids)
        self.assertGreaterEqual(len(observed_goals), 10)

    def test_health_education_renewable_and_digital_roles_use_different_goals(self):
        cases = {
            '29-1141.00': {3},        # Registered Nurses
            '25-2021.00': {4},        # Elementary School Teachers
            '17-2199.11': {7, 9, 13},  # Solar Energy Systems Engineers
            '15-1252.00': {4, 8, 9},  # Software Developers: curated + suggested
        }
        for career_id, expected in cases.items():
            with self.subTest(career_id=career_id):
                data = self.client.post('/api/sdg/mindmap', json={'career_id': career_id}).json()
                self.assertEqual({m['sdg_id'] for m in data['mappings']}, expected)

    def test_unknown_title_cannot_be_explored(self):
        self.assertEqual(self.search('the invalid'), [])
        self.assertEqual(self.client.post('/api/sdg/mindmap', json={'title': 'the invalid'}).status_code, 422)
        self.assertEqual(self.client.post('/api/sdg/mindmap', json={'career_id': 'the invalid'}).status_code, 404)
        self.assertEqual(get_sdg_alignment('the invalid')['status'], 'unknown')
        self.assertEqual(get_sdg_alignment('the invalid')['mappings'], [])

    def test_ambiguous_and_fuzzy_inputs_are_only_suggestions(self):
        choices = self.search('analyst')
        self.assertGreater(len(choices), 1)
        self.assertTrue(all(item['matched_by'] == 'partial' for item in choices))
        fuzzy = self.search('enviromental engineer')
        self.assertEqual(fuzzy[0]['id'], '17-2081.00')
        self.assertEqual(fuzzy[0]['matched_by'], 'suggestion')
        self.assertEqual(get_sdg_alignment('enviromental engineer')['status'], 'unknown')

    def test_empty_oversized_and_unknown_ids_are_handled(self):
        for payload, code in (
            ({}, 422), ({'career_id': ''}, 422), ({'career_id': '   '}, 404),
            ({'career_id': 'x' * 101}, 422), ({'career_id': '99-9999.99'}, 404),
            ({'career_id': 'prototype:data-analyst', 'skills': {'SQL': 5}}, 422),
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post('/api/sdg/mindmap', json=payload).status_code, code)
        self.assertEqual(self.client.get('/api/sdg/careers', params={'q': 'x' * 101}).status_code, 422)
        self.assertLessEqual(len(self.search('')), 12)


if __name__ == '__main__':
    unittest.main()
