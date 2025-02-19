import pandas as pd

# Load the data
data = pd.read_csv('liz.csv')

# Calculate gender ratio
gender_counts = data['GENDER'].value_counts(normalize=True)
female_to_male_ratio = gender_counts.get('FEMALE', 0) / gender_counts.get('MALE', 1)

# Calculate number of ORGAN_FLAG
organ_flag_count = data['ORGAN_FLAG'].value_counts().get('YES', 0)

print(f"Female to Male Ratio: {female_to_male_ratio:.2f}")
print(f"Number of ORGAN_FLAG: {organ_flag_count}")
