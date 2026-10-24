"""Reskilling careers are dynamically sourced from the Career Test CSV.

The CSV supplies OCCUPATION IDENTITIES and O*NET-SOC codes, not occupational
skill standards. For most occupations, skills are starter *SOC major group*
learning templates. Their 0-5 targets, weights, objectives and estimated hours
are illustrative project heuristics, NOT official O*NET proficiency values.

Five older demo templates remain internally for existing saved users only.
"""
import csv
from pathlib import Path

from ._prototype_catalog import CAREERS as LEGACY_CAREERS, DAYS, skill

DATASET = Path(__file__).resolve().parent.parent / 'career_profiles_clean.csv'

# Each group has its own 5 skill domains: (name, safe learning objective, mini-project).
# These are category-level starter templates, not evidence-based career requirements.
GROUPS = {
    '11': ('Management', [
        ('Strategic Planning', 'Compare project goals and priorities', 'Write a short strategy brief'),
        ('Team Coordination', 'Design clear roles and handovers', 'Create a hypothetical team workflow'),
        ('Resource Planning', 'Estimate time and resource requirements', 'Prepare a small resource plan'),
        ('Decision Analysis', 'Evaluate alternatives with stated assumptions', 'Build a simple decision matrix'),
        ('Stakeholder Communication', 'Present a recommendation clearly', 'Create a one-page stakeholder update')]),
    '13': ('Business & Financial Operations', [
        ('Business Research', 'Find and assess reliable business information', 'Summarise a sample business scenario'),
        ('Spreadsheet Analysis', 'Use formulas and organised data tables', 'Create a simple spreadsheet report'),
        ('Budgeting Fundamentals', 'Estimate and explain a sample budget', 'Prepare an illustrative cost worksheet'),
        ('Process Improvement', 'Map workflow and identify opportunities', 'Draw a hypothetical process improvement map'),
        ('Professional Reporting', 'Communicate evidence-based findings', 'Write an executive summary')]),
    '15': ('Computer & Mathematical', [
        ('Programming Foundations', 'Understand functions and basic data handling', 'Build a small Python script'),
        ('Data & Systems Thinking', 'Describe data flows and system components', 'Draw a sample data flow diagram'),
        ('Testing & Debugging', 'Check results using repeatable tests', 'Write a short test checklist'),
        ('Version Control', 'Record and explain project changes', 'Create a Git repository with a README'),
        ('Technical Communication', 'Explain a technical decision', 'Document a simple system design')]),
    '17': ('Architecture & Engineering', [
        ('Technical Mathematics', 'Apply measurements and quantitative reasoning', 'Solve a sample design calculation'),
        ('Design Documentation', 'Interpret a schematic or layout safely', 'Annotate a conceptual design drawing'),
        ('Systems Thinking', 'Identify components and constraints', 'Build a conceptual systems diagram'),
        ('Project Planning', 'Set milestones and track assumptions', 'Draft a sample project schedule'),
        ('Quality & Safety Principles', 'Describe professional safety and quality standards', 'Write a safety-focused checklist')]),
    '19': ('Science & Research', [
        ('Research Methods', 'Formulate a testable research question', 'Write a mini research proposal'),
        ('Data Analysis', 'Organise and describe a sample dataset', 'Analyse a synthetic dataset'),
        ('Statistics Foundations', 'Interpret variability and relationships', 'Create an explanatory statistics summary'),
        ('Scientific Writing', 'Report assumptions and uncertainty', 'Write a short research abstract'),
        ('Research Ethics', 'Recognise ethical use of evidence and data', 'Draft a research ethics checklist')]),
    '21': ('Community & Social Services', [
        ('Needs Assessment', 'Identify needs with respectful questions', 'Develop a sample needs survey'),
        ('Active Listening', 'Practise clear, empathetic communication', 'Write a hypothetical communication script'),
        ('Ethics & Boundaries', 'Recognise professional responsibilities', 'Create a professional boundaries checklist'),
        ('Programme Planning', 'Set goals and evaluation criteria', 'Draft a community support plan'),
        ('Recordkeeping', 'Organise information with privacy in mind', 'Design a fictional case note template')]),
    '23': ('Legal', [
        ('Legal Research Literacy', 'Identify and compare reliable legal sources', 'Summarise publicly available guidance'),
        ('Clear Writing', 'Structure a factual written explanation', 'Draft a fictional issue summary'),
        ('Evidence Organisation', 'Distinguish facts from assumptions', 'Build a mock evidence index'),
        ('Professional Ethics', 'Recognise confidentiality and ethical duties', 'Create an ethics checklist'),
        ('Case Organisation', 'Plan a research workflow and milestones', 'Prepare a sample case timeline')]),
    '25': ('Education', [
        ('Lesson Planning', 'Write measurable learning objectives', 'Design a sample lesson plan'),
        ('Learning Assessment', 'Construct fair formative questions', 'Write a short knowledge quiz'),
        ('Inclusive Teaching', 'Design accessible learning activities', 'Adapt a fictional classroom activity'),
        ('Curriculum Organisation', 'Sequence lessons from basics to advanced', 'Create a four-week topic outline'),
        ('Communication & Feedback', 'Give clear and constructive feedback', 'Write feedback for a sample assignment')]),
    '27': ('Arts, Design & Media', [
        ('Creative Briefs', 'Translate an audience need into a concept', 'Write a creative brief'),
        ('Visual Communication', 'Explain design and layout choices', 'Make a small concept board'),
        ('Audience Research', 'Assess preferences and user needs', 'Draft a research summary'),
        ('Portfolio Development', 'Document a creative process', 'Prepare an annotated portfolio piece'),
        ('Feedback & Iteration', 'Evaluate work against a rubric', 'Create a revision plan')]),
    '29': ('Healthcare Practitioners', [
        ('Health Science Foundations', 'Describe relevant health science concepts at a basic level', 'Make a study concept map'),
        ('Evidence Appraisal', 'Compare health information using credible sources', 'Summarise a public research abstract'),
        ('Professional Communication', 'Practise respectful, clear explanations', 'Prepare a fictional communication scenario'),
        ('Ethics & Privacy', 'Explain confidentiality and professional standards', 'Write a patient privacy checklist'),
        ('Documentation Literacy', 'Organise simulated records accurately', 'Design a fictional documentation template')]),
    '31': ('Healthcare Support', [
        ('Health Communication', 'Practise clear supportive communication', 'Write a fictional support dialogue'),
        ('Health & Hygiene Theory', 'Summarise guidance from reputable sources', 'Prepare a general hygiene awareness poster'),
        ('Recordkeeping', 'Explain accurate, private recordkeeping', 'Design a fictional activity log'),
        ('Team Coordination', 'Identify professional boundaries and escalation roles', 'Draw a support team roles diagram'),
        ('Workplace Safety Awareness', 'Recognise general workplace hazards', 'Create a general safety awareness checklist')]),
    '33': ('Protective Service', [
        ('Risk Awareness', 'Recognise and report risks in general terms', 'Draft a safe risk-awareness checklist'),
        ('De-escalation Communication', 'Use calm, respectful verbal communication', 'Write a fictional non-confrontational dialogue'),
        ('Incident Documentation', 'Record factual observations clearly', 'Prepare a fictional incident log'),
        ('Ethics & Public Responsibility', 'Discuss fairness and privacy', 'Create a professional conduct guide'),
        ('Coordination & Planning', 'Describe team responsibilities', 'Draw a hypothetical communication workflow')]),
    '35': ('Food Preparation & Serving', [
        ('Food Safety Theory', 'Explain general food hygiene principles', 'Make a food-safety infographic'),
        ('Food Preparation Knowledge', 'Compare common preparation methods conceptually', 'Create a sample recipe comparison'),
        ('Menu Planning', 'Balance constraints and preferences', 'Design a fictional weekly menu'),
        ('Inventory Planning', 'Estimate ingredient quantities and costs', 'Build a sample inventory worksheet'),
        ('Food Waste Reduction', 'Identify ways to reduce waste', 'Plan a kitchen sustainability poster')]),
    '37': ('Building & Grounds Maintenance', [
        ('Workplace Safety Awareness', 'Recognise general safety principles', 'Create a hazard-awareness checklist'),
        ('Maintenance Scheduling', 'Organise routine tasks and checks', 'Draft a sample maintenance calendar'),
        ('Sustainable Practices', 'Compare resource-saving alternatives', 'Create a water-saving proposal'),
        ('Inspection Documentation', 'Write clear fictional inspection notes', 'Build a sample inspection form'),
        ('Service Communication', 'Explain maintenance plans respectfully', 'Draft a customer update')]),
    '39': ('Personal Care & Service', [
        ('Client Communication', 'Practise respectful professional exchanges', 'Write a fictional client conversation'),
        ('Service Planning', 'Identify preferences and time constraints', 'Create a sample service plan'),
        ('Hygiene & Safety Awareness', 'Explain general health and safety responsibilities', 'Prepare a safety-awareness poster'),
        ('Scheduling & Records', 'Organise bookings and keep notes confidential', 'Build a sample appointment tracker'),
        ('Professional Conduct', 'Identify fairness, consent and privacy', 'Create a service ethics checklist')]),
    '41': ('Sales', [
        ('Customer Needs Research', 'Identify a target audience and requirements', 'Create a customer persona'),
        ('Ethical Communication', 'Explain product features clearly', 'Write a transparent sales message'),
        ('Product Comparison', 'Compare offerings with an objective rubric', 'Make a product comparison table'),
        ('CRM & Documentation', 'Organise simulated customer interactions', 'Create a fictional CRM spreadsheet'),
        ('Performance Analytics', 'Interpret basic conversion measures', 'Build a sample sales dashboard')]),
    '43': ('Office & Administrative Support', [
        ('Document Management', 'Structure and organise office records', 'Create a document naming standard'),
        ('Spreadsheets', 'Use formulas and maintain accurate tables', 'Build a practice spreadsheet'),
        ('Scheduling', 'Organise multiple deadlines', 'Design a sample office calendar'),
        ('Digital Tools', 'Use common workplace productivity tools', 'Create a practice workflow guide'),
        ('Professional Communication', 'Write clear emails and updates', 'Draft a fictional work email')]),
    '45': ('Farming, Fishing & Forestry', [
        ('Sustainability Awareness', 'Recognise resource-management tradeoffs', 'Create a sustainability plan'),
        ('Environmental Fundamentals', 'Describe basic ecological relationships', 'Make an environmental concept map'),
        ('Data Logging', 'Organise environmental observations', 'Build a sample observation log'),
        ('Resource Planning', 'Estimate time and material needs', 'Make a simple planning worksheet'),
        ('Safety & Compliance Theory', 'Identify why professional standards matter', 'Prepare a safety-focused checklist')]),
    '47': ('Construction & Extraction', [
        ('Drawing Interpretation', 'Recognise common layout and measurement conventions', 'Annotate a sample plan'),
        ('Measurement & Estimation', 'Calculate basic quantities from safe examples', 'Complete a practice estimation worksheet'),
        ('Material Knowledge', 'Compare material properties conceptually', 'Make a materials comparison chart'),
        ('Project Coordination', 'Describe tasks and scheduling dependencies', 'Draft a milestone plan'),
        ('Safety & Regulations', 'Explain general professional safety duties', 'Prepare a safety awareness poster')]),
    '49': ('Installation, Maintenance & Repair', [
        ('Systems Reasoning', 'Identify components and dependencies', 'Draw a simplified system diagram'),
        ('Diagnostic Thinking', 'Organise evidence and possible explanations', 'Draft a hypothetical diagnostic decision tree'),
        ('Work Documentation', 'Write clear maintenance notes', 'Create a fictional service record'),
        ('Quality Assurance', 'Describe verification and inspection concepts', 'Develop a QA checklist'),
        ('Safety Principles', 'Understand general safety responsibilities', 'Write a safety awareness summary')]),
    '51': ('Production', [
        ('Process Mapping', 'Describe an orderly production workflow', 'Draw a conceptual process chart'),
        ('Quality Control', 'Interpret basic quality measurements', 'Build a mock QC worksheet'),
        ('Production Analytics', 'Organise output and efficiency metrics', 'Create a sample production dashboard'),
        ('Workplace Safety Theory', 'Recognise general workplace precautions', 'Prepare a safety awareness poster'),
        ('Team Coordination', 'Plan communication and handoffs', 'Draw a shift handover template')]),
    '53': ('Transportation & Material Moving', [
        ('Logistics Planning', 'Compare route and schedule constraints', 'Create a hypothetical delivery schedule'),
        ('Recordkeeping', 'Organise shipment-related records', 'Build a fictional tracking sheet'),
        ('Compliance & Safety Theory', 'Describe general professional safety obligations', 'Make a safety checklist'),
        ('Time Management', 'Prioritise commitments and deadlines', 'Develop a sample time plan'),
        ('Customer Coordination', 'Write clear and professional updates', 'Draft a delivery status message')]),
}

# Fallback for any future O*NET-SOC major group not yet covered.
FALLBACK = ('General Career Development', [
    ('Digital Literacy', 'Organise information using common digital tools', 'Create a digital information summary'),
    ('Communication', 'Present ideas clearly', 'Write a professional briefing'),
    ('Problem Solving', 'Compare alternatives and assumptions', 'Create a simple decision matrix'),
    ('Project Planning', 'Break a goal into feasible tasks', 'Plan a mini-project'),
    ('Information Research', 'Find and evaluate reliable sources', 'Write a source comparison'),
])


def template_for_family(code):
    """Build a distinct illustrative 5-skill family pathway."""
    family, items = GROUPS.get(code[:2], FALLBACK)
    competencies = {}
    for index, (name, objective, project) in enumerate(items):
        # Explicit example values. None are verified by occupational studies.
        competencies[name] = skill(
            required=3 if index % 3 else 4,
            importance=round(0.85 + (4 - index) * 0.025, 3),
            hours=5 if index % 2 == 0 else 4,
            objective=objective,
            project=project,
        )
    return family, competencies


def load_career_catalog(csv_path=DATASET):
    """Build one selectable pathway per occupation row (deduped by title).

    If user supplies a 293-row compatible Career Test CSV later, the list also
    becomes 293, without changing reskilling functions or HTML.
    """
    roles = {}
    with Path(csv_path).open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        if not {'Title', 'O*NET-SOC Code'}.issubset(fields):
            raise ValueError('Career Test CSV needs Title and O*NET-SOC Code columns')
        for row in reader:
            title = (row.get('Title') or '').strip()
            code = (row.get('O*NET-SOC Code') or '').strip()
            if not title or not code or title in roles:
                continue
            family, skills = template_for_family(code)
            roles[title] = {
                'description': f'Starter learning pathway for the {family} occupation family.',
                'family': family, 'soc_code': code,
                'source_type': 'occupation-family example',
                'source_note': ('Career title and O*NET-SOC code are loaded from the Career Test CSV. '
                                'The five learning skills, suggested 0–5 targets, weights and hours '
                                'are illustrative family-level examples, not official occupational requirements.'),
                'skills': skills,
            }
    if not roles:
        raise ValueError('No valid occupation titles found in Career Test CSV')
    # Preserve occupation titles and accept Career Test names verbatim.
    return dict(sorted(roles.items(), key=lambda item: item[0].casefold()))


# All official-looking titles come from the user's actual dataset; 5 older
# example career names stay internal only to avoid breaking saved demo sessions.
MATCHING_CAREERS = load_career_catalog()

# Prefer exact-code O*NET ratings, when the user has installed official CSV files.
# If none exist, the original family-level prototypes remain available and labelled.
from .onet_profiles import apply_onet_profiles
ONET_IMPORT_REPORT = apply_onet_profiles(MATCHING_CAREERS)

CAREERS = dict(LEGACY_CAREERS)
CAREERS.update(MATCHING_CAREERS)


def public_catalog():
    """Frontend Target Career dropdown exactly matches the Career Test CSV."""
    return {
        name: {
            'description': role['description'],
            'family': role['family'], 'soc_code': role['soc_code'],
            'source_type': role['source_type'], 'source_note': role['source_note'],
            'skills': {
                skill_name: {
                    'required': detail['required'],
                    'importance': detail['importance'],
                    'data_source': detail.get('data_source', role.get('source_type', 'example')),
                    **({'onet_importance': detail['onet_importance']} if 'onet_importance' in detail else {}),
                    **({'onet_task_id': detail['onet_task_id']} if 'onet_task_id' in detail else {}),
                }
                for skill_name, detail in role['skills'].items()
            },
        }
        for name, role in MATCHING_CAREERS.items()
    }


# Existing targeted corrections stay highest priority. They are manually curated
# illustrative modules, not official proficiency measurements.
from .occupation_skill_overrides import apply_overrides
CURATED_OVERRIDES = apply_overrides(CAREERS)
for _name in CURATED_OVERRIDES:
    if _name in MATCHING_CAREERS:
        _role = MATCHING_CAREERS[_name]
        _role['source_type'] = 'curated occupation-specific learning example'
        _role['source_note'] = (
            'Skills and learning projects are occupation-focused examples informed '
            'by occupational descriptions. Required levels, weights and hours '
            'have not been validated as O*NET standards.'
        )

# Final coverage report uses final profiles, including manually curated examples.
ONET_IMPORT_REPORT['upgraded'] = sum(
    r.get('source_type', '').startswith('O*NET 31.0')
    for r in MATCHING_CAREERS.values()
)
ONET_IMPORT_REPORT['family_fallback'] = sum(
    r.get('source_type') == 'occupation-family example'
    for r in MATCHING_CAREERS.values()
)
ONET_IMPORT_REPORT['curated_overrides'] = sum(
    r.get('source_type') == 'curated occupation-specific learning example'
    for r in MATCHING_CAREERS.values()
)
ONET_IMPORT_REPORT['total'] = len(MATCHING_CAREERS)
ONET_IMPORT_REPORT['rated_and_task'] = sum(
    r.get('source_type', '').startswith('O*NET 31.0 rated skills + occupation tasks')
    for r in MATCHING_CAREERS.values()
)
ONET_IMPORT_REPORT['task_only'] = sum(
    r.get('source_type', '').startswith('O*NET 31.0 occupation tasks')
    for r in MATCHING_CAREERS.values()
)
ONET_IMPORT_REPORT['rated_only'] = sum(
    r.get('source_type', '').startswith('O*NET 31.0 rated skills (')
    for r in MATCHING_CAREERS.values()
)
