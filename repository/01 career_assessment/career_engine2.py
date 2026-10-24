#在它（名字）后面加这个

from ai_development_trends import (
    get_ai_trend_report,
    analyze_career_impact
)
from career_engine import forecast_category

result = forecast_category("AI & Data Science")

# 获取完整AI趋势报告
ai_report = get_ai_trend_report()

# 分析特定职业受AI影响
career_impact = analyze_career_impact(
    "Data Scientist"
)

print(career_impact)
print(result["direction"])
print(result["major_drivers"])
print(result["future_skills"])
