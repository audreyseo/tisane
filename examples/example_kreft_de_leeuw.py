import tisane as ts

import pandas as pd
import numpy as np
import random

"""
Example from Kreft & de Leeuw, 1989
"""
student = ts.Nominal("Student")
school = ts.Nominal("School")
math = ts.Numeric("MathAchievement")
hw = ts.Numeric("HomeWork")
race = ts.Nominal("Race")
ses = ts.Numeric("SES")
mean_ses = ts.Numeric("MeanSES")

# Conceptual relationships
hw.causes(math)
race.associates_with(math)
ses.associates_with(
    math
)  # TODO: Transitive cause should be something Tisane surface/suggests to user?
mean_ses.associates_with(math)  # Should be transitive

# Data measurement relationships
student.has(hw)
student.has(race)
student.has(ses)

# school.has(mean_ses)
# student.nest_under(school)

math_data = np.random.randn(1, 50)
# hw_data = np.random.randint(1,50) + 1
hw_data = np.random.randint(0, 24, size=50)
ses_data = np.random.randn(1, 50) * 10000
mean_ses_data = np.random.randn(1, 50) * 10000
race_data = random.choices(["White", "Hispanic", "Black", "Asian", "Indigenous"], k=50)
#
# Data source, use synthetic data
data = pd.DataFrame(
    {
        "MathAchievement": math_data.tolist()[0],
        "HomeWork": hw_data.tolist(),
        "Race": race_data,
        "SES": ses_data[0],
        "MeanSES": mean_ses_data[0],
    }
)

design = ts.Design(
    dv=math,
    ivs=[hw],
    # ivs = [hw, race, ses, mean_ses],
    source=data,
)

ts.infer_statistical_model_from_design(design=design)
