"""Canonical occupational identities; SDG coverage is a separate concern."""
import csv
import json
from functools import lru_cache
from pathlib import Path
from reskilling.catalog import CAREERS

BASE = Path(__file__).resolve().parent
ALIASES = {
    'environmental engineer': 'onet:17-2081.00',
    'software developer': 'onet:15-1252.00',
    'information security analyst': 'onet:15-1212.00',
}


def normalize(value):
    return ' '.join(value.casefold().split())


@lru_cache(maxsize=1)
def catalogue():
    with (BASE / 'career_profiles_clean.csv').open(encoding='utf-8-sig', newline='') as source:
        records = [{'id': 'onet:' + row['O*NET-SOC Code'], 'title': row['Title'],
                    'kind': 'occupation'} for row in csv.DictReader(source)]
    # Prototype roles are not silently equated with occupations.
    records.extend({'id': 'prototype:' + normalize(title).replace(' ', '-'),
                    'title': title, 'kind': 'prototype'} for title in CAREERS)
    return {item['id']: item for item in records}


@lru_cache(maxsize=1)
def reviewed_mappings():
    entries = json.loads((BASE / 'sdg_reviewed_mappings.json').read_text(encoding='utf-8'))
    result = {}
    for entry in entries:
        if entry['career_id'] not in catalogue():
            raise ValueError('Reviewed mapping refers to unknown career')
        for goal in entry['goals']:
            if not (1 <= goal['id'] <= 17) or not goal['target_id'].startswith(str(goal['id']) + '.'):
                raise ValueError('Invalid SDG target')
            if not all(goal.get(key) for key in ('reason', 'evidence', 'limitations', 'reviewed_at')):
                raise ValueError('Reviewed mapping requires evidence and review metadata')
        result[entry['career_id']] = entry['goals']
    return result


def public_record(item):
    return {**item, 'mapping_status': 'reviewed' if reviewed_mappings().get(item['id']) else 'not_reviewed'}


def resolve_title(title):
    key = normalize(title)
    matches = [item for item in catalogue().values() if normalize(item['title']) == key]
    if len(matches) == 1:
        return matches[0]
    alias = ALIASES.get(key)
    return catalogue().get(alias) if not matches else None


def search(query, limit=20):
    key = normalize(query)
    if not key:
        return []
    alias = ALIASES.get(key)
    hits = [item for item in catalogue().values()
            if all(word in normalize(item['title']) for word in key.split()) or item['id'] == alias]
    hits.sort(key=lambda item: (normalize(item['title']) != key, item['id'] != alias, item['title']))
    return [public_record(item) for item in hits[:limit]]
