"""Functional API checks for the single-server integrated prototype."""
import os
import tempfile
import unittest
import base64

# Must be configured before importing reskilling.api, which creates Store.
TEST_DATA = tempfile.TemporaryDirectory(prefix='futureskill_test_')
os.environ['FUTURESKILL_DATA_DIR'] = TEST_DATA.name

from fastapi.testclient import TestClient
from app import app
from assessment_scoring import RIASEC, SUBJECTS, SKILLS


class IntegratedWebTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_both_pages_and_assets(self):
        old = self.client.get('/')
        self.assertEqual(old.status_code, 200)
        self.assertIn('Start Career Assessment', old.text)
        self.assertIn('reskilling?career=', old.text)
        new = self.client.get('/reskilling')
        self.assertEqual(new.status_code, 200)
        self.assertIn('Generate my pathway', new.text)
        self.assertIn('careerBridgeNote', new.text)
        self.assertEqual(self.client.get('/reskill-static/app.js').status_code, 200)
        self.assertEqual(self.client.get('/reskill-static/style.css').status_code, 200)

    def test_original_career_assessment(self):
        payload = {
            'answers': {d: [4, 3, 4, 5] for d in RIASEC},
            'subject_answers': {d: [5, 3] for d in SUBJECTS},
            'skill_answers': {d: 3 for d in SKILLS},
        }
        result = self.client.post('/api/recommend', json=payload)
        self.assertEqual(result.status_code, 200, result.text)
        body = result.json()
        self.assertEqual(len(body['recommendations']), 10)
        self.assertIn('riasec_scores', body)
        self.assertEqual(len(body['riasec_scores']), 6)

    def test_reskilling_full_journey(self):
        state = self.client.get('/api/state').json()
        csrf = state['csrf']
        skills = {name: 0 for name in state['catalog']['Data Analyst']['skills']}
        profile = {
            'target_career': 'Data Analyst', 'skills': skills,
            'user_type': 'student', 'current_industry': 'education',
            'experience': 'beginner', 'personal_goal': 'Data portfolio',
            'weekly_hours': 6, 'target_weeks': 8,
            'preferred_days': ['Tuesday', 'Thursday', 'Saturday'],
            'learning_style': 'project',
        }
        headers = {'X-CSRF-Token': csrf}
        denied = self.client.post('/api/plan', json=profile)
        self.assertEqual(denied.status_code, 403)
        result = self.client.post('/api/plan', json=profile, headers=headers)
        self.assertEqual(result.status_code, 200, result.text)
        body = result.json()['state']
        self.assertIn('SQL', body['gaps'])
        self.assertGreater(len(body['tasks']), 0)
        task = body['tasks'][0]
        completed = self.client.post(f"/api/tasks/{task['id']}/status", json={'completed': True}, headers=headers)
        self.assertEqual(completed.status_code, 200)
        self.assertGreater(completed.json()['state']['tree']['points'], 0)

        # Valid tiny PNG fixture: no Pillow or third-party image package required.
        tiny_png = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/bP8AAAAASUVORK5CYII='
        )
        proof = self.client.post(f"/api/tasks/{task['id']}/proof", headers=headers,
                                 files={'photo': ('practice.png', tiny_png, 'image/png')})
        self.assertEqual(proof.status_code, 200, proof.text)
        fetched = self.client.get(f"/api/tasks/{task['id']}/proof")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.headers['content-type'], 'image/png')

        replan = self.client.post('/api/replan', json={
            'weekly_hours': 4, 'target_weeks': 10, 'preferred_days': ['Monday', 'Saturday']}, headers=headers)
        self.assertEqual(replan.status_code, 200, replan.text)
        new_state = replan.json()['state']
        self.assertTrue(any(t['id'] == task['id'] and t['completed'] for t in new_state['tasks']))
        self.assertEqual(new_state['tree']['points'], completed.json()['state']['tree']['points'])

        second = TestClient(app)
        other_state = second.get('/api/state').json()
        self.assertIsNone(other_state['profile'])
        stolen = second.post(f"/api/tasks/{task['id']}/status", json={'completed': True},
                             headers={'X-CSRF-Token': other_state['csrf']})
        self.assertEqual(stolen.status_code, 404)
        private_photo = second.get(f"/api/tasks/{task['id']}/proof")
        self.assertEqual(private_photo.status_code, 404)


if __name__ == '__main__':
    unittest.main()
