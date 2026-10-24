"""Functional API checks for the single-server integrated prototype."""
import os
import tempfile
import unittest
import base64
import re
from urllib.parse import parse_qs, urlparse

# Must be configured before importing reskilling.api, which creates Store.
TEST_DATA = tempfile.TemporaryDirectory(prefix='futureskill_test_')
os.environ['FUTURESKILL_DATA_DIR'] = TEST_DATA.name
os.environ['FUTURESKILL_DEV_INVENTORY'] = '1'

from fastapi.testclient import TestClient
from main import app
from assessment_scoring import RIASEC, SUBJECTS, SKILLS


class IntegratedWebTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_shared_brand_asset(self):
        asset = self.client.get('/static/futureskill-atom.svg')
        self.assertEqual(asset.status_code, 200)
        self.assertIn('image/svg+xml', asset.headers['content-type'])
        self.assertIn('<ellipse', asset.text)
        shell = self.client.get('/static/future-theme.js').text
        self.assertIn('/static/futureskill-atom.svg?v=1', shell)
        for route, selector in (
            ('/reskilling', 'class="brand-icon"'),
            ('/sdg-impact', 'class="brand-mark"'),
        ):
            page = self.client.get(route)
            self.assertEqual(page.status_code, 200)
            self.assertIn(selector, page.text)
            self.assertIn('/static/futureskill-atom.svg?v=1', page.text)
            self.assertNotIn('>✳</span>', page.text)
            self.assertNotIn('>FS</span>', page.text)

    def test_shared_theme_on_every_existing_page(self):
        for route, page in (
            ('/', 'home'), ('/reskilling', 'reskilling'), ('/ai-trend', 'trends'),
            ('/uncertainty', 'uncertainty'), ('/sdg-impact', 'sdg'), ('/__dev/screens', 'inventory'),
        ):
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'data-futureskill-page="{page}"', response.text)
            for asset in ('future-theme.js', 'future-theme.css', 'future-pages.css'):
                self.assertRegex(response.text, rf'/static/{re.escape(asset)}\?v=[A-Za-z0-9_-]+')
            self.assertLess(response.text.index('/static/future-theme.js'),
                            response.text.index('/static/future-theme.css'))
            self.assertNotIn('__FUTURE_PREVIEW__', response.text)
        for asset in ('future-theme.js', 'future-theme.css', 'future-pages.css'):
            response = self.client.get(f'/static/{asset}')
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('/__mockup/', response.text)
            self.assertNotIn('fixtures', response.text)

    def test_both_pages_and_assets(self):
        old = self.client.get('/')
        self.assertEqual(old.status_code, 200)
        self.assertIn('Start Career Assessment', old.text)
        self.assertIn('reskilling?career=', old.text)
        new = self.client.get('/reskilling')
        self.assertEqual(new.status_code, 200)
        self.assertIn('Generate my pathway', new.text)
        self.assertIn('careerBridgeNote', new.text)
        for label in (
            'Overview', 'My Reskilling Plan', 'Progress Tracking',
            'AI &amp; Career Trends', 'Explore Careers', 'SDG Alignment', 'Settings',
        ):
            self.assertIn(label, new.text)
        for element_id in (
            'workspaceSidebar', 'workspaceToggle', 'workspaceNav',
            'settingsDialog', 'themePreference', 'beginSetup', 'sdgNavLink',
        ):
            self.assertIn(f'id="{element_id}"', new.text)
        self.assertIn('href="/ai-trend"', new.text)
        self.assertIn('id="sdgNavLink" data-nav-sdg href="/sdg-impact"', new.text)
        self.assertIn('CV import', new.text)
        self.assertIn('Cross-device sync', new.text)
        self.assertEqual(self.client.get('/reskill-static/app.js').status_code, 200)
        self.assertEqual(self.client.get('/reskill-static/style.css').status_code, 200)

    def test_imported_github_feature_prototypes(self):
        homepage = self.client.get('/')
        self.assertIn('Explore More Features', homepage.text)
        self.assertIn('href="/ai-trend"', homepage.text)
        self.assertEqual(self.client.get('/ai-trend').status_code, 200)
        self.assertIn('Not a validated forecast', self.client.get('/ai-trend').text)
        self.assertEqual(self.client.get('/uncertainty').status_code, 200)
        self.assertIn('not employment forecasts', self.client.get('/uncertainty').text)
        lab = self.client.get('/uncertainty').text
        for item in ('Employment-to-Population Ratio', 'id="employmentChart"',
                     'id="yearTable"', 'No validated uncertainty interval is available',
                     '/static/uncertainty-chart.js', '/static/uncertainty-chart.css'):
            self.assertIn(item, lab)
        for asset in ('uncertainty-chart.js', 'uncertainty-chart.css'):
            self.assertEqual(self.client.get(f'/static/{asset}').status_code, 200)
        self.assertEqual(self.client.get('/sdg-impact').status_code, 200)
        sdg_page = self.client.get('/sdg-impact').text
        self.assertIn('Potential alignment is not impact', sdg_page)
        self.assertIn('Show more', sdg_page)
        self.assertIn('node(article, "dialog"', sdg_page)
        self.assertIn('mapping-drawer-panel', sdg_page)
        self.assertIn('Official SDG icon from the United Nations', sdg_page)
        for element_id in ('goalGrid', 'mapLines', 'goalInfoDialog', 'careerCenter'):
            self.assertIn(f'id="{element_id}"', sdg_page)
        self.assertIn('Read all full evidence wording', sdg_page)
        self.assertIn('evidence-map', sdg_page)
        self.assertIn('/static/assets/sdg/sdg-4-education.jpg', sdg_page)
        self.assertIn('/static/assets/sdg/sdg-8-work.jpg', sdg_page)
        self.assertIn('mapping.supporting_evidence', sdg_page)
        self.assertIn('mapping.impact_limitations', sdg_page)
        for asset in (
            '/static/assets/sdg/sdg-4-icon.png',
            '/static/assets/sdg/sdg-8-icon.png',
            '/static/assets/sdg/sdg-4-education.jpg',
            '/static/assets/sdg/sdg-8-work.jpg',
        ):
            self.assertEqual(self.client.get(asset).status_code, 200)

        trend_data = self.client.get('/api/ai-trends').json()
        self.assertEqual(len(trend_data['categories']), 10)
        self.assertFalse(trend_data['quantitative_employment_forecast'])
        self.assertIn('limitations', trend_data)

        scenarios = self.client.get('/api/uncertainty/scenarios').json()
        self.assertEqual(len(scenarios['scenarios']), 6)
        self.assertIn('not calibrated', scenarios['warning'])
        first_scenario = scenarios['scenarios'][0]
        pictured_scenario = next(item for item in scenarios['scenarios'] if item['id'] == 'C')
        self.assertEqual(pictured_scenario['employment_rate']['2031'], 72.39)
        simulation = self.client.post('/api/uncertainty/simulate', json={
            **first_scenario['inputs'],
            'base_rate': scenarios['base_rate'],
        })
        self.assertEqual(simulation.status_code, 200, simulation.text)
        self.assertIn('2031', simulation.json()['employment_rate'])
        self.assertIn('not calibrated', simulation.json()['warning'])
        invalid_simulation = self.client.post('/api/uncertainty/simulate', json={
            **first_scenario['inputs'], 'ai_growth': 101,
        })
        self.assertEqual(invalid_simulation.status_code, 422)

        mapping = self.client.post('/api/sdg/mindmap', json={
            'career_id': 'prototype:data-analyst',
        })
        self.assertEqual(mapping.status_code, 200, mapping.text)
        mapping_data = mapping.json()
        self.assertEqual(mapping_data['status'], 'suggested')
        self.assertEqual(
            [item['target_id'] for item in mapping_data['learning_pathway_mappings']],
            ['4.4', '8.5'],
        )
        self.assertTrue(mapping_data['pathway_skills'])
        self.assertIn('illustrative', mapping_data['evidence_scope'])
        self.assertEqual(mapping_data['pathway_career'], 'Data Analyst')
        sql = next(item for item in mapping_data['pathway_skills'] if item['name'] == 'SQL')
        self.assertIsNone(sql['current_level'])

        unconfirmed_skills = self.client.post('/api/sdg/mindmap', json={
            'career_id': 'prototype:data-analyst',
            'skills': {'SQL': 2},
        })
        self.assertEqual(unconfirmed_skills.status_code, 422)

        alias = self.client.post('/api/sdg/mindmap', json={
            'career_id': '15-1252.00',
        })
        self.assertEqual(alias.status_code, 200, alias.text)
        self.assertEqual(alias.json()['pathway_career'], 'Software Developer')

        unreviewed = self.client.post('/api/sdg/mindmap', json={
            'career_id': '17-2081.00',
        })
        self.assertEqual(unreviewed.status_code, 200, unreviewed.text)
        self.assertEqual(unreviewed.json()['status'], 'suggested')
        self.assertEqual({item['sdg_id'] for item in unreviewed.json()['mappings']}, {6, 9, 13})
        self.assertEqual(
            self.client.post('/api/sdg/mindmap', json={'career_id': ''}).status_code,
            422,
        )

    def test_sdg_goal_exploration_does_not_invent_career_links(self):
        for goal in range(1, 18):
            with self.subTest(goal=goal):
                image = self.client.get(f'/static/assets/sdg/sdg-{goal}-icon.png')
                self.assertEqual(image.status_code, 200)
                self.assertEqual(image.headers['content-type'], 'image/png')
                self.assertTrue(image.content.startswith(b'\x89PNG\r\n\x1a\n'))

        for career, career_id in (
            ('Data Analyst', 'prototype:data-analyst'),
            ('Software Developer', '15-1252.00'),
            ('Cybersecurity Analyst', 'prototype:cybersecurity-analyst'),
            ('UI/UX Designer', 'prototype:ui-ux-designer'),
            ('Digital Marketing Specialist', 'prototype:digital-marketing-specialist'),
        ):
            with self.subTest(career=career):
                data = self.client.post('/api/sdg/mindmap', json={'career_id': career_id}).json()
                self.assertEqual(data['status'], 'suggested')
                self.assertEqual(
                    {(item['sdg_id'], item['target_id']) for item in data['learning_pathway_mappings']},
                    {(4, '4.4'), (8, '8.5')},
                )
                self.assertTrue(all(item['supporting_evidence'] for item in data['learning_pathway_mappings']))
                self.assertTrue(all(item['sdg_id'] not in {4, 8} for item in data['mappings']))

        # The reference mockup is not evidence for assigning its sample links.
        unknown = self.client.post('/api/sdg/mindmap', json={
            'career_id': '17-2081.00',
        }).json()
        self.assertEqual(unknown['status'], 'suggested')
        self.assertEqual({item['sdg_id'] for item in unknown['mappings']}, {6, 9, 13})
        self.assertEqual(unknown['pathway_skills'], [])

    def test_development_inventory_and_isolated_demo_sessions(self):
        inventory = self.client.get('/__dev/screens')
        self.assertEqual(inventory.status_code, 200)
        self.assertIn('S24', inventory.text)
        self.assertIn('AI Trend Explorer', inventory.text)

        demo = self.client.get('/__dev/demo/open?scenario=default&screen=S10')
        self.assertEqual(demo.status_code, 200)
        self.assertIn('demo=1', str(demo.url))
        sample_state = self.client.get('/api/state?demo=1&demo_scenario=default').json()
        self.assertIsNotNone(sample_state['profile'])
        self.assertTrue(any(task['proof_url'] for task in sample_state['tasks']))

        regular_state = self.client.get('/api/state').json()
        self.assertIsNone(regular_state['profile'])

        self.client.get('/__dev/demo/open?scenario=no-gap&screen=S16')
        no_gap = self.client.get('/api/state?demo=1&demo_scenario=no-gap').json()
        self.assertEqual(no_gap['stats']['remaining_hours'], 0)
        self.assertEqual(no_gap['tasks'], [])

        self.client.get('/__dev/demo/open?scenario=partial&screen=S17')
        partial = self.client.get('/api/state?demo=1&demo_scenario=partial').json()
        self.assertGreater(partial['stats']['remaining_hours'], 0)
        self.assertGreater(len(partial['tasks']), 0)

        returning = self.client.get(
            '/__dev/demo/open?scenario=returning&screen=S15&career=Software%20Developers'
        )
        self.assertEqual(returning.status_code, 200)
        self.assertEqual(
            parse_qs(urlparse(str(returning.url)).query)['career'],
            ['Software Developers'],
        )
        returning_state = self.client.get(
            '/api/state?demo=1&demo_scenario=returning'
        ).json()
        self.assertEqual(returning_state['profile']['target_career'], 'Data Analyst')

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
        self.assertTrue(all(
            isinstance(item.get('sdg_alignment'), dict)
            for item in body['recommendations']
        ))
        self.assertTrue(all(
            item['sdg_alignment']['status'] in ('curated', 'suggested')
            for item in body['recommendations']
        ))

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
