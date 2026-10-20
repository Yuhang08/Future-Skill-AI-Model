
import pandas as pd

# 1. Load the official O*NET CSV file
df = pd.read_csv(r"career_interest_types.csv")

# 2. Keep only numeric RIASEC profiles
df = df[df["Scale ID"] == "OI"].copy()

# 3. Keep the latest record for each occupation and RIASEC type
df["Date"] = pd.to_datetime(
    df["Date"],
    format="%b-%y",
    errors="coerce"
)

df = df.sort_values("Date")

df = df.drop_duplicates(
    subset=["O*NET-SOC Code", "Element Name"],
    keep="last"
)

# 4. Map interest names to RIASEC letters
name_to_letter = {
    "Realistic": "R",
    "Investigative": "I",
    "Artistic": "A",
    "Social": "S",
    "Enterprising": "E",
    "Conventional": "C"
}

df["RIASEC"] = df["Element Name"].map(name_to_letter)

df = df.dropna(subset=["RIASEC", "Data Value"])

# 5. Convert long-format data into six columns
careers = df.pivot(
    index=["O*NET-SOC Code", "Title"],
    columns="RIASEC",
    values="Data Value"
).reset_index()

# 6. Ensure all six dimensions exist
for dimension in ["R", "I", "A", "S", "E", "C"]:
    if dimension not in careers.columns:
        careers[dimension] = pd.NA

# 7. Keep occupations with all six scores
careers = careers.dropna(
    subset=["R", "I", "A", "S", "E", "C"]
)

# 8. Calculate each occupation's top three types
dimensions = ["R", "I", "A", "S", "E", "C"]

careers["RIASEC_Top3"] = careers.apply(
    lambda row: "".join(
        sorted(
            dimensions,
            key=lambda d: row[d],
            reverse=True
        )[:3]
    ),
    axis=1
)

# 9. Save the cleaned dataset
careers.to_csv(r"career_profiles_clean.csv", index=False)

print("Data processing complete!")
print(f"Number of occupations: {len(careers)}")

print(
    careers[
        ["Title", "R", "I", "A", "S", "E", "C", "RIASEC_Top3"]
    ].head(10).to_string(index=False)
)
