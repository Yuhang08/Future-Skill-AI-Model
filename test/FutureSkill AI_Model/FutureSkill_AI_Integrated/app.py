"""Standalone Flask HR Interview; add these /api/interview routes to your existing app if merging."""
import os, time, uuid, threading
from flask import Flask, request, jsonify, render_template, make_response
from dotenv import load_dotenv
from career_data import get_careers, find_career
from history_store import init, all_text, insert, global_count
from interview_engine import initial_question, generate_question, feedback_for, report, adaptive_plan
from semantic_validator import check_question, embed
from question_policy import exact_duplicate,word_duplicate
from speech_service import transcribe
load_dotenv()
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=11*1024*1024
init()
sessions={}; lock=threading.RLock(); TTL=3600
MODES={'HR','Technical','Mixed'}
LANGUAGES={'English','中文'}

def fail(message,code=400):return jsonify(error=message),code

def guest_id():
    """Cookie ID is random/opaque, never supplied by user request body."""
    val=request.cookies.get('fs_guest')
    if val and len(val)==64 and all(c in '0123456789abcdef' for c in val):return val
    return None

def ensure_guest(resp,gid):
    if not guest_id():
        resp.set_cookie('fs_guest',gid,httponly=True,secure=request.is_secure,
                        samesite='Lax',max_age=365*24*3600)
    return resp

def session(data):
    sid=str(data.get('session_id',''))
    with lock:
        s=sessions.get(sid)
        if s and (time.time()-s['created']>TTL or s['guest']!=guest_id()):return None
        return s

def cache_embedding(question):
    # Persisted DB embedding cache can replace this simple request/session cache.
    return embed(question)

@app.get('/')
def home():return render_template('interview.html')

@app.get('/api/careers')
def careers():
    items=get_careers()
    return jsonify(careers=[x['title'] for x in items],count=len(items),
                   source='career_profiles_clean.csv' if os.path.exists('career_profiles_clean.csv') else 'careers_demo.csv')

@app.get('/api/interview/history-count')
def count_history():
    return jsonify(personal_count=len(all_text(guest_id())) if guest_id() else 0,global_count=global_count())

@app.post('/api/interview/start')
def start():
    data=request.get_json(silent=True) or {}
    role=str(data.get('role',''))
    mode=str(data.get('mode','Mixed'))
    language=str(data.get('language','English'))
    try:nq=int(data.get('question_count',5))
    except (ValueError,TypeError):return fail('Invalid question count')
    if not find_career(role):return fail('Choose a career in the database')
    if mode not in MODES or language not in LANGUAGES or nq not in (3,5,10):return fail('Invalid configuration')
    if not os.getenv('OPENAI_API_KEY'):return fail('Configure OPENAI_API_KEY',503)
    gid=guest_id() or uuid.uuid4().hex+uuid.uuid4().hex
    sid=uuid.uuid4().hex; previous=all_text(gid)
    facts=find_career(role)
    try:
        q=pick(role,mode,language,facts,previous,[],None)
    except Exception:
        app.logger.exception('Question generation failed');return fail('Could not generate a verified question',503)
    with lock:
        sessions[sid]={'created':time.time(),'guest':gid,'role':role,'mode':mode,'language':language,
                       'question':q,'history':[],'awaiting_next':False,'max_questions':nq,'previous':previous,'facts':facts}
    resp=make_response(jsonify(session_id=sid,question_number=1,max_questions=nq,**q))
    return ensure_guest(resp,gid)

def pick(role,mode,language,facts,previous,current,adaptive):
    # Full semantic checks only on previous 100 (or all if under 150) and current session.
    # All older questions still checked for exact duplicate.
    recent_answer=adaptive.get('last_answer','') if adaptive else ''
    difficulty=adaptive.get('difficulty','standard') if adaptive else 'standard'
    focus_history=previous[-20:]+current
    for attempt in range(3):
        q=generate_question(role,mode,language,focus_history,facts,difficulty,recent_answer)
        text=q['question']
        approved,reason=check_question(text,previous,current,cache_embedding)
        if approved:
            # In production also add a distinct fact-check of user claims + sources.
            return q
        focus_history.append(text)
    raise ValueError('All generated questions were too similar; add curated fallback questions')

@app.post('/api/interview/transcribe')
def transcript():
    s=session(request.form)
    if not s:return fail('Session expired',404)
    audio=request.files.get('audio')
    if not audio:return fail('Audio missing')
    try:return jsonify(transcript=transcribe(audio))
    except Exception:
        app.logger.exception('Transcription failed');return fail('Cannot transcribe audio',503)

@app.post('/api/interview/feedback')
def feedback():
    data=request.get_json(silent=True) or {}; s=session(data)
    if not s:return fail('Session expired',404)
    answer=str(data.get('answer','')).strip()
    if not 3<=len(answer)<=3500:return fail('Answer must be 3–3500 characters')
    with lock:
        if s['awaiting_next']:return fail('Already answered',409)
        s['awaiting_next']=True
    try:
        fb=feedback_for(s['question']['question'],answer,s['role'],s['mode'],s['language'])
        with lock:
            s['history'].append({'question':s['question']['question'],'answer':answer,'feedback':fb})
            # No answers, transcript, or audio stored on server database.
            insert(s['guest'],str(data['session_id']),s['question']['question'],s['role'])
        return jsonify(feedback=fb,finished=len(s['history'])>=s['max_questions'])
    except Exception:
        with lock:s['awaiting_next']=False
        app.logger.exception('Feedback failed');return fail('Feedback generation failed',503)

@app.post('/api/interview/next')
def next_question():
    data=request.get_json(silent=True) or {};s=session(data)
    if not s:return fail('Session expired',404)
    if not s['awaiting_next']:return fail('Submit your answer first',409)
    if len(s['history'])>=s['max_questions']:
        rep=report(s['history'],s['role'],s['language'])
        return jsonify(finished=True,report=rep)
    past=list(s['history']); adaptive=adaptive_plan(past)
    adaptive['last_answer']=past[-1]['answer']
    try:
        question=pick(s['role'],s['mode'],s['language'],s['facts'],s['previous'],
                      [i['question'] for i in past],adaptive)
    except Exception:
        app.logger.exception('Next question failed');return fail('No non-repeating question was found',503)
    s['question']=question;s['awaiting_next']=False
    return jsonify(finished=False,question_number=len(past)+1,max_questions=s['max_questions'],**question)

@app.post('/api/interview/end')
def end():
    data=request.get_json(silent=True) or {};s=session(data)
    if not s:return fail('Session expired',404)
    if not s['history']:return fail('Answer a question first')
    rep=report(s['history'],s['role'],s['language'])
    with lock:sessions.pop(str(data['session_id']),None)
    return jsonify(report=rep)

@app.errorhandler(413)
def large(_):return fail('Maximum upload 10MB',413)

if __name__=='__main__':app.run(port=5000,debug=False)
