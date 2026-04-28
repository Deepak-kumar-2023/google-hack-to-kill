"""
FairGuard AI — Sample Data Generator
Creates a synthetic hiring dataset with known biases for demonstration.
"""

import pandas as pd
import numpy as np
import os


def generate_hiring_dataset(n=5000, output_path=None):
    """Generate a synthetic hiring dataset with embedded biases."""
    np.random.seed(42)

    # Demographics
    gender = np.random.choice(['Male', 'Female'], n, p=[0.62, 0.38])
    race = np.random.choice(
        ['White', 'Black', 'Hispanic', 'Asian'],
        n, p=[0.55, 0.18, 0.17, 0.10]
    )
    age = np.clip(np.random.normal(35, 10, n).astype(int), 21, 65)

    # Qualifications
    education = np.random.choice(
        ['High School', 'Bachelor', 'Master', 'PhD'],
        n, p=[0.20, 0.45, 0.25, 0.10]
    )
    experience = np.clip(np.random.normal(8, 5, n).astype(int), 0, 30)
    skill_score = np.clip(np.random.normal(70, 15, n).astype(int), 20, 100)
    interview_score = np.clip(np.random.normal(65, 20, n).astype(int), 10, 100)

    edu_map = {'High School': 0, 'Bachelor': 1, 'Master': 2, 'PhD': 3}
    edu_num = np.array([edu_map[e] for e in education])

    # Base hiring probability
    base_prob = (
        0.15 +
        edu_num * 0.12 +
        np.clip(experience / 30, 0, 1) * 0.25 +
        np.clip(skill_score / 100, 0, 1) * 0.25 +
        np.clip(interview_score / 100, 0, 1) * 0.20
    )

    # EMBED BIASES
    gender_bias = np.where(gender == 'Female', -0.15, 0.05)
    race_bias = np.zeros(n)
    race_bias[race == 'White'] = 0.08
    race_bias[race == 'Black'] = -0.18
    race_bias[race == 'Hispanic'] = -0.10
    race_bias[race == 'Asian'] = 0.02
    age_bias = np.where((age > 50) | (age < 25), -0.08, 0.03)

    final_prob = np.clip(base_prob + gender_bias + race_bias + age_bias, 0.05, 0.95)
    hired = (np.random.random(n) < final_prob).astype(int)

    df = pd.DataFrame({
        'applicant_id': range(1, n + 1),
        'gender': gender,
        'race': race,
        'age': age,
        'education': education,
        'experience_years': experience,
        'skill_score': skill_score,
        'interview_score': interview_score,
        'hired': hired
    })

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Generated {n} records -> {output_path}")

    return df


if __name__ == '__main__':
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sample_hiring_data.csv')
    df = generate_hiring_dataset(output_path=path)
    print(f"\nDataset shape: {df.shape}")
    print(f"Hire rate: {df['hired'].mean():.1%}")
    print(f"\nHire rate by gender:\n{df.groupby('gender')['hired'].mean()}")
    print(f"\nHire rate by race:\n{df.groupby('race')['hired'].mean()}")
