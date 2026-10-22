import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('FUTURESKILL_DATA_DIR', tempfile.mkdtemp(prefix='fs-catalogue-'))
from fastapi.testclient import TestClient
from app import app
from career_catalogue import catalogue, resolve_title, search


class CareerCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_canonical_alias_and_search(self):
        for title in ['Environmental Engineer', ' environmental   ENGINEER ', 'Environmental Engineers']:
            self.assertEqual(resolve_title(title)['id'], 'onet:17-2081.00')
        response = self.client.get('/api/careers', params={'q': 'environmental engineer'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(r['id'] == 'onet:17-2081.00' for r in response.json()['results']))
        self.assertGreater(len(catalogue()), 900)

    def test_unknown_and_bounds(self):
        for data in [{'title':'the invalid'}, {'title':''}, {'career_id':'bad', 'title':'Environmental Engineer'}, {'title':'x'*121}]:
            self.assertEqual(self.client.post('/api/sdg/mindmap', json=data).status_code, 422)
        self.assertEqual(self.client.get('/api/careers', params={'q':'x'*121}).status_code, 422)
        self.assertEqual(self.client.get('/api/careers', params={'limit':1000}).status_code, 422)
        self.assertEqual(search('the invalid'), [])

    def test_unreviewed_suggestions_are_not_reviewed(self):
        result = self.client.post('/api/sdg/mindmap', json={'career_id':'onet:17-2081.00'}).json()
        self.assertEqual(result['goals'], [])
        self.assertEqual(result['mapping_status'], 'not_reviewed')
        self.assertEqual({g['id'] for g in result['suggestions']}, {9,13})
        self.assertTrue(all(g['provisional'] for g in result['suggestions']))
        self.assertEqual(len(result['all_goals']), 17)
        self.assertEqual(result['skills'], [])

    def test_known_unmapped_and_prototype(self):
        role = search('Data Analyst')[0]
        self.assertTrue(role['id'].startswith('prototype:'))
        result = self.client.post('/api/sdg/mindmap', json={'career_id':role['id']}).json()
        self.assertEqual(result['goals'], [])
        self.assertEqual(result['suggestions'], [])
        self.assertEqual(result['mapping_status'], 'not_reviewed')

    def test_reviewed_data_preserved_separately(self):
        mapping = {'id':4,'target_id':'4.4','reason':'Test fixture', 'evidence':['fixture'],
                   'limitations':'Fixture, not a production claim','reviewed_at':'2026-10-22'}
        with patch('app.reviewed_mappings', return_value={'onet:17-2081.00':[mapping]}), patch('career_catalogue.reviewed_mappings', return_value={'onet:17-2081.00':[mapping]}):
            result = self.client.post('/api/sdg/mindmap', json={'career_id':'onet:17-2081.00'}).json()
            self.assertEqual(result['mapping_status'], 'reviewed')
            self.assertEqual(result['goals'][0]['target_id'], '4.4')
            self.assertFalse(result['goals'][0]['provisional'])
