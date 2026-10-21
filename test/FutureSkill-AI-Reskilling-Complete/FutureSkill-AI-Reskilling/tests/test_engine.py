import base64
import http.client
import json
import tempfile
import threading
import unittest
from datetime import date
from pathlib import Path
from http.server import ThreadingHTTPServer
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import InputError, generate_schedule, skill_gaps, tree_details, validate_profile
from catalog import CAREERS


def sample_profile():
    return {
        "user_type":"student", "current_industry":"Education",
        "experience":"beginner", "target_career":"Data Analyst",
        "personal_goal":"Build my first portfolio",
        "skills":{skill:0 for skill in CAREERS["Data Analyst"]["skills"]},
        "weekly_hours":6, "target_weeks":8,
        "preferred_days":["Tuesday","Thursday","Saturday"],
        "learning_style":"project",
    }


class TestAlgorithm(unittest.TestCase):
    def test_skill_gap_and_priority(self):
        p = validate_profile(sample_profile())
        p["skills"]["SQL"] = 2
        p["skills"]["Excel"] = 5
        gaps = skill_gaps(p)
        self.assertEqual(gaps["SQL"]["gap"], 2)
        self.assertEqual(gaps["SQL"]["estimated_hours"], 10)
        self.assertEqual(gaps["Excel"]["gap"], 0)
        self.assertEqual(gaps["Excel"]["priority"], 0)

    def test_all_skills_complete_no_tasks(self):
        p=sample_profile()
        p["skills"] = {s:info["required"] for s, info in CAREERS["Data Analyst"]["skills"].items()}
        plan = generate_schedule(validate_profile(p),start_day=date(2026,10,20))
        self.assertEqual(plan["estimated_total_hours"], 0)
        self.assertEqual(plan["tasks"], [])

    def test_schedule_days_budget(self):
        p=validate_profile(sample_profile())
        result = generate_schedule(p,start_day=date(2026,10,20))
        per_week = {}
        for task in result["tasks"]:
            per_week[task["week_index"]] = per_week.get(task["week_index"],0) + task["hours"]
            self.assertIn(task["day"],p["preferred_days"])
        for hours in per_week.values():
            self.assertLessEqual(hours, p["weekly_hours"]+0.06)
        self.assertGreater(len(result["tasks"]),0)

    def test_prerequisites_scheduled_before_dependent(self):
        p=sample_profile()
        p["target_weeks"]=32
        plan=generate_schedule(validate_profile(p),start_day=date(2026,10,20))
        names=[t["skill"] for t in plan["tasks"] if t["kind"]=="learning"]
        self.assertLess(names.index('Python Basics'),names.index('Pandas'))
        self.assertLess(names.index('Pandas'),names.index('Data Visualisation'))
        last_basics=max(i for i,s in enumerate(names) if s=='Python Basics')
        self.assertLess(last_basics, names.index('Pandas'))

    def test_replanning_respects_completed_hours(self):
        p=validate_profile(sample_profile())
        base=generate_schedule(p,start_day=date(2026,10,20))
        changed=generate_schedule(p,{"SQL":10},start_day=date(2026,10,20))
        self.assertAlmostEqual(base["remaining_before_plan"]-changed["remaining_before_plan"], 10)

    def test_input_validations(self):
        p=sample_profile();p["preferred_days"]=[]
        with self.assertRaises(InputError):validate_profile(p)
        p=sample_profile();p["skills"]["SQL"]=7
        with self.assertRaises(InputError):validate_profile(p)
        p=sample_profile();p["weekly_hours"]=0
        with self.assertRaises(InputError):validate_profile(p)
        p=sample_profile();p["target_career"]="Fake"
        with self.assertRaises(InputError):validate_profile(p)

    def test_tree_stages(self):
        self.assertEqual(tree_details(0)["name"], "Seed")
        self.assertEqual(tree_details(10)["name"], "Sprout")
        self.assertEqual(tree_details(35)["name"], "Seedling")
        self.assertEqual(tree_details(80)["name"], "Young tree")
        self.assertEqual(tree_details(250)["name"], "Learning forest")


class TestHttpIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app
        cls.app=app
        cls.tmp=tempfile.TemporaryDirectory()
        app.STORE=app.Store(Path(cls.tmp.name)/'db.sqlite3')
        app.UPLOADS=Path(cls.tmp.name)/'uploads'
        app.UPLOADS.mkdir()
        cls.httpd=ThreadingHTTPServer(('127.0.0.1',0), app.Handler)
        cls.port=cls.httpd.server_address[1]
        cls.thread=threading.Thread(target=cls.httpd.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)
        cls.tmp.cleanup()

    def setUp(self):
        self.cookie = None
        self.csrf = ''

    def request(self, method, path, data=None, content_type='application/json', csrf=True):
        headers={}
        if self.cookie:headers['Cookie']=self.cookie
        if method=='POST' and csrf:headers['X-CSRF-Token']=self.csrf
        if data is not None:
            headers['Content-Type']=content_type
            if content_type=='application/json': data=json.dumps(data).encode()
        connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=8)
        connection.request(method,path,body=data,headers=headers)
        r=connection.getresponse()
        raw=r.read();status=r.status
        sent_cookie=r.getheader('Set-Cookie')
        if sent_cookie:self.cookie=sent_cookie.split(';',1)[0]
        if 'application/json' in (r.getheader('Content-Type') or ''):
            data=json.loads(raw)
            if 'csrf' in data:self.csrf=data['csrf']
        else:data=raw
        connection.close()
        return status,data

    def test_create_complete_replan_and_photo(self):
        status,state=self.request('GET','/api/state')
        self.assertEqual(status,200)
        self.assertIsNone(state['profile'])
        status,result=self.request('POST','/api/plan',sample_profile())
        self.assertEqual(status,200,result)
        self.assertGreater(len(result['state']['tasks']),0)
        first=next(t for t in result['state']['tasks'] if t['kind']=='learning')
        self.assertFalse(first['completed'])
        status,complete=self.request('POST',f'/api/tasks/{first["id"]}/status',{'completed':True})
        self.assertEqual(status,200)
        self.assertTrue(complete['state']['tree']['points']>0)
        initial_points=complete['state']['tree']['points']

        status,replan=self.request('POST','/api/replan',{
            'weekly_hours':3,'target_weeks':20,'preferred_days':['Monday','Saturday']
        })
        self.assertEqual(status,200,replan)
        self.assertEqual(replan['state']['tree']['points'],initial_points)
        self.assertTrue(any(t['id']==first['id'] and t['completed'] for t in replan['state']['tasks']))
        self.assertEqual(replan['state']['profile']['weekly_hours'],3)

        # Minimal valid self-contained PNG sample with matching PNG magic/IEND.
        png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/lr8AAAAASUVORK5CYII=')
        boundary='----FS-TEST-BOUNDARY'
        multipart=(f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="proof.png"\r\nContent-Type: image/png\r\n\r\n').encode()+png+f'\r\n--{boundary}--\r\n'.encode()
        status,upload=self.request('POST',f'/api/tasks/{first["id"]}/proof',multipart,f'multipart/form-data; boundary={boundary}')
        self.assertEqual(status,200,upload)
        task=next(t for t in upload['state']['tasks'] if t['id']==first['id'])
        status,photo=self.request('GET',task['proof_url'])
        self.assertEqual(status,200)
        self.assertEqual(photo,png)

    def test_separate_sessions_and_csrf(self):
        status,state=self.request('GET','/api/state')
        self.assertEqual(status,200)
        status,result=self.request('POST','/api/plan',sample_profile(),csrf=False)
        self.assertEqual(status,403)
        status,result=self.request('POST','/api/plan',sample_profile())
        self.assertEqual(status,200)
        owned=result['state']['tasks'][0]['id']
        old_cookie=self.cookie
        self.cookie=None
        self.csrf=''
        status,other=self.request('GET','/api/state')
        self.assertEqual(status,200)
        self.assertNotEqual(self.cookie,old_cookie)
        self.assertIsNone(other['profile'])
        status,result=self.request('POST',f'/api/tasks/{owned}/status',{'completed':True})
        self.assertEqual(status,404)


if __name__=='__main__':unittest.main()
