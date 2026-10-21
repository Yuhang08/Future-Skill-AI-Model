"""FutureSkill AI: educational scenario-based employment forecast.
No training or empirically calibrated predictions are implied.
Run: python uncertainty_engine.py
"""
from dataclasses import dataclass

YEARS = list(range(2026, 2032))
BASE_EMPLOYMENT_RATE = 68.9  # illustrative starting value, change to validated data

@dataclass(frozen=True)
class Scenario:
    name: str
    ai_growth: float       # 0-100: AI innovation speed
    automation: float      # 0-100: automation adoption intensity
    adaptation: float      # 0-100: worker transition capacity
    economy: float         # 0-100: economic conditions (50 neutral)
    alignment: float       # 0-100: misalignment severity (0 safest)
    other_factors: float = 50  # demographics, policies, etc. (50 neutral)

SCENARIOS = {
    "A": Scenario("Balanced Growth", 85, 65, 85, 85, 10, 60),
    "B": Scenario("AI Fast, Economy Slow", 85, 80, 35, 25, 15, 45),
    "C": Scenario("Traditional Economic Boom", 25, 30, 65, 85, 10, 60),
    "D": Scenario("Dual Stagnation", 20, 25, 30, 20, 10, 40),
    "E": Scenario("Over-Automation", 95, 95, 20, 70, 20, 50),
    "F": Scenario("Goal Misalignment", 85, 75, 50, 60, 90, 50),
}

# Occupational growth sensitivity coefficients are illustrative, not fitted.
# Each tuple is (economy, AI opportunities, automation displacement, alignment disruptions).
JOBS = {
    "AI Engineer": (0.40, 0.90, 0.10, 0.40),
    "Software Developer": (0.55, 0.50, 0.35, 0.35),
    "Nurse": (0.40, 0.08, 0.08, 0.12),
    "Construction Worker": (0.85, 0.05, 0.30, 0.08),
    "Factory Assembly Worker": (0.70, 0.05, 0.90, 0.20),
    "Administrative Clerk": (0.45, 0.02, 0.95, 0.10),
    "Cybersecurity Specialist": (0.55, 0.65, 0.10, -0.20),
    "Electrician": (0.65, 0.15, 0.15, 0.06),
    "Cleaner": (0.40, 0.02, 0.55, 0.08),
    "Teacher": (0.38, 0.08, 0.20, 0.12),
}

def annual_rate_change(s: Scenario) -> float:
    """Annual change in employment-to-population ratio, in percentage points.

    Transparent assumed response coefficients. This is NOT an estimated model.
    AI growth influences job opportunities only through economy/automation here.
    """
    economic_effect = 0.018 * (s.economy - 50)
    general_effect = 0.005 * (s.other_factors - 50)
    transition_gap = max(0, s.automation - s.adaptation)
    displacement_effect = -0.012 * transition_gap
    alignment_effect = -0.003 * s.alignment
    tech_opportunity = 0.003 * s.ai_growth * s.adaptation / 100
    return economic_effect + general_effect + displacement_effect + alignment_effect + tech_opportunity

def employment_forecast(s: Scenario, base_rate: float = BASE_EMPLOYMENT_RATE):
    rate = base_rate
    result = {YEARS[0]: round(rate, 2)}
    for year in YEARS[1:]:
        rate = max(0.0, min(100.0, rate + annual_rate_change(s)))
        result[year] = round(rate, 2)
    return result

def occupational_growth(s: Scenario):
    """Illustrative annual occupational headcount growth percentages.

    Different from the national employment-to-population ratio.
    """
    results = {}
    for job, (econ_w, ai_w, auto_w, align_w) in JOBS.items():
        # Scale to rough annual percentages for UI illustration.
        growth = (0.06 * econ_w * (s.economy - 50)
                  + 0.035 * ai_w * s.ai_growth
                  - 0.045 * auto_w * max(0, s.automation - 0.4 * s.adaptation)
                  - 0.02 * align_w * s.alignment
                  + 0.008 * (s.other_factors - 50))
        results[job] = round(growth, 2)
    return results

if __name__ == "__main__":
    print("FutureSkill AI | Scenario-Based Employment Simulation")
    print("WARNING: Model outputs are illustrative, not validated forecasts.\n")
    for code, s in SCENARIOS.items():
        predicted = employment_forecast(s)
        print(f"{code}. {s.name:29s} 2031 employment rate: {predicted[2031]:.2f}%")
    print("\nExample scenario E occupational annual growth assumptions:")
    for job, change in occupational_growth(SCENARIOS["E"]).items():
        print(f"  {job:27s}: {change:+.2f}%")
