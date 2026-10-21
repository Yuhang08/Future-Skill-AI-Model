"""Run this Flask app locally: python app.py"""
from flask import Flask, jsonify, render_template, request
from uncertainty_engine import SCENARIOS, Scenario, employment_forecast, occupational_growth

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("uncertainty.html")

@app.get("/api/scenarios")
def scenarios():
    return jsonify({key: {
        "name": scenario.name,
        "employment_rate": employment_forecast(scenario),
        "occupational_growth": occupational_growth(scenario)
    } for key, scenario in SCENARIOS.items()})

@app.post("/api/simulate")
def simulate():
    data = request.get_json(silent=True) or {}
    fields = ["ai_growth", "automation", "adaptation", "economy", "alignment", "other_factors"]
    try:
        values = {k: float(data[k]) for k in fields}
        if any(not (0 <= v <= 100) for v in values.values()):
            raise ValueError("All values must be between 0 and 100")
        base_rate = float(data.get("base_rate", 68.9))
        if not (0 <= base_rate <= 100):
            raise ValueError("base_rate must be between 0 and 100")
    except (ValueError, TypeError, KeyError) as error:
        return jsonify({"error": str(error)}), 400
    scenario = Scenario("Custom", **values)
    return jsonify({
        "employment_rate": employment_forecast(scenario, base_rate),
        "occupational_growth": occupational_growth(scenario)
    })

if __name__ == "__main__":
    app.run(debug=True)
