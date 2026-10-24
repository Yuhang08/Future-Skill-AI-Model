"""FutureSkill AI: explainable, occupation-specific reskilling profiles.

Reads O*NET 31.0 OFFLINE CSV files from reskilling/onet_data/. Supports
knowledge.csv, essential_skills.csv, transferable_skills.csv,
task_statements.csv and task_ratings.csv.

Facts: only exact O*NET-SOC code matches, original task descriptions,
       original IM (importance) ratings on their 1..5 scale.
Heuristics: attaching tasks to learning objectives/projects, suggested goals,
       practice hours, assumed self-assessment targets, weights, sample projects.

O*NET 31.0 Database by USDOL/ETA, CC BY 4.0, modified by FutureSkill AI.
https://www.onetcenter.org/database.html
https://www.onetcenter.org/license_db.html
Not approved, endorsed, or tested by USDOL/ETA.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / 'onet_data'
RATING_FILES = {
    'Knowledge': 'knowledge.csv',
    'Essential Skills': 'essential_skills.csv',
    'Transferable Skills': 'transferable_skills.csv',
}
OTHER_FILES = ('task_statements.csv', 'task_ratings.csv')


def _locate(directory, basename):
    if not directory.is_dir():
        return None
    for path in directory.iterdir():
        if path.is_file() and path.name.lower() == basename:
            return path
    return None


def _read_rows(path, required):
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                f'{path.name}: incorrect CSV headers; expected {sorted(required)}. '
                'Use original O*NET 31.0 CSV, not a renamed Excel file.'
            )
        yield from reader


def _code(value):
    return str(value or '').strip().upper()


def _normalize(label):
    return re.sub(r'[^a-z0-9]+', '', label.casefold())


def _number(text):
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def _read_ratings(path):
    """Occupation -> (element name -> official importance IM 1..5)."""
    records = defaultdict(dict)
    required = {'O*NET-SOC Code', 'Element Name', 'Scale ID', 'Data Value'}
    for row in _read_rows(path, required):
        if (row.get('Scale ID') or '').strip() != 'IM':
            continue
        if (row.get('Recommend Suppress') or '').upper().strip() == 'Y':
            continue
        if (row.get('Not Relevant') or '').upper().strip() == 'Y':
            continue
        code = _code(row.get('O*NET-SOC Code'))
        label = (row.get('Element Name') or '').strip()
        score = _number(row.get('Data Value'))
        if code and label and score is not None and 1 <= score <= 5:
            records[code][label] = max(score, records[code].get(label, 0))
    return records


def _read_tasks(path):
    records = defaultdict(list)
    required = {'O*NET-SOC Code', 'Task ID', 'Task'}
    for row in _read_rows(path, required):
        code = _code(row.get('O*NET-SOC Code'))
        task_id = (row.get('Task ID') or '').strip()
        text = ' '.join((row.get('Task') or '').split())
        kind = (row.get('Task Type') or '').strip()
        if code and task_id and text:
            records[code].append({
                'id': task_id, 'text': text, 'type': kind,
                'importance': None,
            })
    return records


def _read_task_importance(path):
    records = {}
    required = {'O*NET-SOC Code', 'Task ID', 'Scale ID', 'Data Value'}
    for row in _read_rows(path, required):
        if (row.get('Scale ID') or '').strip() != 'IM':
            continue
        if (row.get('Recommend Suppress') or '').upper().strip() == 'Y':
            continue
        score = _number(row.get('Data Value'))
        if score is None or not 1 <= score <= 5:
            continue
        key = (_code(row.get('O*NET-SOC Code')), (row.get('Task ID') or '').strip())
        if key[0] and key[1]:
            records[key] = score
    return records


def _common_record(title, name, importance, domain):
    """FutureSkill examples, NOT O*NET proficiency standards."""
    return {
        'required': 4 if importance >= 4.0 else 3,
        'importance': round(importance / 5.0, 3),
        'hours_per_level': 5,
        'objective': (
            f'Explain the principles of {name} and apply them to a '
            f'hypothetical {title} workplace scenario.'
        ),
        'project': (
            f'Create a small fictional case study showing how {name} matters '
            f'in {title}; include assumptions and a source reference.'
        ),
        'prerequisites': [],
        'data_source': f'O*NET 31.0 {domain}, importance (IM)',
        'onet_importance': importance,
    }


# Avoid converting hazardous duties into suggested physical practice.
SENSITIVE = re.compile(
    r'\b(weapon|firearm|explosive|ammunition|grenade|surgery|surgical|'
    r'controlled substance|hazardous chemical|toxic substance|'
    r'flight control|operate aircraft)\b', re.I
)


def _sorted_tasks(source_tasks, code):
    """Order exact-code O*NET statements; importance is used only as ranking evidence."""
    return sorted(source_tasks.get(code, []), key=lambda task: (
        -(task['importance'] if task['importance'] is not None else
          (3.5 if task['type'].casefold() == 'core' else 2.0)),
        task['type'].casefold() != 'core',
        task['id'],
    ))


# These transparent aliases improve loose alignment of *skills* to *tasks*.
# The alignment is a heuristic, never an official O*NET task-to-skill mapping.
TERM_ALIASES = {
    'accounting': {'accounts', 'account', 'financial', 'finance', 'reconcile', 'audit'},
    'mathematics': {'quantitative', 'calculation', 'calculate', 'statistics', 'mathematical'},
    'medicine': {'patient', 'medical', 'health', 'clinical', 'diagnosis'},
    'education': {'teaching', 'student', 'learning', 'curriculum', 'training'},
    'fine': {'design', 'creative', 'perform', 'audition', 'arts'},
    'management': {'manage', 'coordinate', 'supervise', 'plan'},
    'safety': {'compliance', 'hazard', 'risk', 'inspection', 'secure'},
    'service': {'customer', 'client', 'support', 'service'},
    'communication': {'explain', 'discuss', 'present', 'report', 'speak'},
    'data': {'analysis', 'analyze', 'information', 'records', 'statistics'},
}
STOPWORDS = {'and','the','for','with','from','that','this','using','into','their','them',
             'which','such','other','work','activity','apply','understand','skills',
             'knowledge','information','perform','provide','use','maintain'}


def _terms(text):
    words = set(re.findall(r'[a-z]{4,}', text.casefold())) - STOPWORDS
    for concept, related in TERM_ALIASES.items():
        if concept in words or bool(words & related):
            words.add(concept)
    return words


def _attach_task_evidence(title, skills, tasks, *, max_tasks=3):
    """Link occupational tasks to learning activities, not to self-rated skills.

    Task assignments are approximate and identified as such. All tasks are real
    O*NET statements matched by exact occupation code (where installed).
    """
    if not skills or not tasks:
        return 0
    assigned_skills = set()
    assigned = 0
    skill_names = list(skills)
    for task in tasks:
        if assigned >= min(max_tasks, len(skill_names)):
            break
        remaining = [n for n in skill_names if n not in assigned_skills]
        if not remaining:
            break
        task_terms = _terms(task['text'])
        # Prefer relevant domains; rotate fairly when no lexical overlap exists.
        name = max(remaining, key=lambda n: (
            len(_terms(n) & task_terms),
            skills[n]['importance'],
            -skill_names.index(n),
        ))
        assigned_skills.add(name)
        detail = skills[name]
        evidence = task['text']
        concise = evidence[:180] + ('…' if len(evidence) > 180 else '')
        detail['onet_task_id'] = task['id']
        detail['task_evidence'] = evidence
        detail['task_skill_link'] = 'heuristic — not an official O*NET task-skill link'
        if task['importance'] is not None:
            detail['onet_task_importance'] = task['importance']
        if SENSITIVE.search(evidence):
            detail['objective'] = (
                f'Explain how {name} relates to professional standards, ethical '
                f'decisions and safe oversight in {title}.'
            )
            detail['project'] = (
                f'Write a non-operational, fictional case review of the professional '
                f'responsibilities associated with this {title} duty: {concise}'
            )
        else:
            detail['objective'] = (
                f'Explain the principles of {name} and how they support this '
                f'{title} work activity: {concise}'
            )
            detail['project'] = (
                f'Create a hypothetical or desk-based {title} case study inspired '
                f'by this task: {concise}. Explain your approach and evaluation criteria.'
            )
        assigned += 1
    return assigned


def _selected_skills(title, code, source_ratings, maximum=8):
    """Select only *knowledge/skill* element names for the questionnaire.

    O*NET tasks must be attached to learning objectives and projects afterward.
    Proficiency targets, practice hours and projects remain FutureSkill examples.
    """
    output = {}
    normalized = set()

    def add(name, detail):
        key = _normalize(name)
        if key in normalized or len(output) >= maximum:
            return False
        normalized.add(key)
        output[name] = detail
        return True

    domain_caps = [('Knowledge', 4), ('Essential Skills', 2), ('Transferable Skills', 2)]
    for domain, cap in domain_caps:
        scored = source_ratings.get(domain, {}).get(code, {})
        added = 0
        for name, importance in sorted(scored.items(), key=lambda x: (-x[1], x[0])):
            if added >= cap or len(output) >= maximum:
                break
            if add(name, _common_record(title, name, importance, domain)):
                added += 1

    if len(output) < 6:
        remaining = []
        for domain in source_ratings:
            remaining += [(im, label, domain)
                          for label, im in source_ratings[domain].get(code, {}).items()]
        for im, label, domain in sorted(remaining, key=lambda x: (-x[0], x[1])):
            if len(output) >= min(6, maximum):
                break
            add(label, _common_record(title, label, im, domain))
    return output


def apply_onet_profiles(roles, data_dir=DATA_DIR):
    """Update each exact-code occupation with rated competencies and task evidence.

    Where ratings are absent, O*NET tasks contextualize clearly-labelled SOC
    starter skills. This does NOT invent validated occupation-specific skills.
    """
    folder = Path(data_dir)
    source_ratings = {}
    source_tasks = {}
    files = []
    for domain, filename in RATING_FILES.items():
        path = _locate(folder, filename)
        if path is not None:
            source_ratings[domain] = _read_ratings(path)
            files.append(filename)
    task_file = _locate(folder, 'task_statements.csv')
    if task_file is not None:
        source_tasks = _read_tasks(task_file)
        files.append('task_statements.csv')
    importance_file = _locate(folder, 'task_ratings.csv')
    if importance_file is not None:
        ratings = _read_task_importance(importance_file)
        files.append('task_ratings.csv')
        for code, tasks in source_tasks.items():
            for task in tasks:
                task['importance'] = ratings.get((code, task['id']))

    report = {
        'total': len(roles), 'loaded_files': files, 'upgraded': 0,
        'rated_and_task': 0, 'task_only': 0, 'rated_only': 0,
        'family_fallback': 0, 'missing_codes': [],
        'tasks_attached_to_projects': 0,
        'official_rated_skill_profiles': 0,
    }
    for title, role in roles.items():
        code = _code(role.get('soc_code'))
        rated = _selected_skills(title, code, source_ratings)
        tasks = _sorted_tasks(source_tasks, code)
        has_rating = bool(rated)
        has_task = bool(tasks)

        if has_rating:
            skills = rated
            if len(skills) < 5:
                # Clearly marked supplementary family skills, *not* O*NET rated.
                for name, record in role['skills'].items():
                    if len(skills) >= 6:
                        break
                    if name not in skills:
                        supplemental = deepcopy(record)
                        supplemental['data_source'] = 'SOC family starter example, unverified'
                        skills[name] = supplemental
            role['skills'] = skills
            report['official_rated_skill_profiles'] += 1
            role['source_type'] = ('O*NET 31.0 rated competencies + task-context projects'
                                   if has_task else 'O*NET 31.0 rated competencies')
            if has_task:
                report['rated_and_task'] += 1
            else:
                report['rated_only'] += 1
        elif has_task:
            # No official rated competencies for this exact occupation code.
            # Keep neutral skills instead of relabeling arbitrary task texts as skills.
            role['skills'] = deepcopy(role['skills'])
            for detail in role['skills'].values():
                detail['data_source'] = 'SOC major-group starter skill — unverified'
            role['source_type'] = 'O*NET task-informed SOC starter competencies (unverified)'
            report['task_only'] += 1
        else:
            role['skills'] = deepcopy(role['skills'])
            for detail in role['skills'].values():
                detail['data_source'] = 'SOC major-group illustrative template'
            role['source_type'] = 'SOC family example — no occupation-level O*NET data'
            report['family_fallback'] += 1
            report['missing_codes'].append((title, code))

        if has_rating or has_task:
            report['upgraded'] += 1
            if has_task:
                report['tasks_attached_to_projects'] += _attach_task_evidence(
                    title, role['skills'], tasks
                )
            role['source_note'] = (
                'Occupation names and original importance-rated competency labels (where '
                'available), plus task statements, come from O*NET 31.0. Task-to-skill '
                'linkages, 0–5 learning targets, study time, learning objectives and projects '
                'are FutureSkill AI heuristics, not verified O*NET training standards. '
                'For task-only occupations, starter skill labels are unverified SOC-family examples.'
            )
    return report
