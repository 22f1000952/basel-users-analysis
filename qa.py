import pandas as pd
import numpy as np
from datetime import datetime
import re

users_df = pd.read_csv('users.csv')
repos_df = pd.read_csv('repositories.csv')

users_df['created_at'] = pd.to_datetime(users_df['created_at'])
repos_df['created_at'] = pd.to_datetime(repos_df['created_at'])

top_followers = users_df.nlargest(5, 'followers')['login'].tolist()
q1 = ','.join(top_followers)

earliest_users = users_df.nsmallest(5, 'created_at')['login'].tolist()
q2 = ','.join(earliest_users)

top_licenses = repos_df['license_name'].value_counts()
top_licenses = top_licenses[top_licenses.index != ''].nlargest(3).index.tolist()
q3 = ','.join(top_licenses)

company_counts = users_df['company'].value_counts()
q4 = company_counts.index[0] if len(company_counts) > 0 else "NONE"

q5 = repos_df['language'].value_counts().index[0]

recent_users = users_df[users_df['created_at'] > '2020-01-01']['login']
recent_repos = repos_df[repos_df['login'].isin(recent_users)]
q6 = recent_repos['language'].value_counts().index[1]

lang_stars = repos_df.groupby('language')['stargazers_count'].mean()
q7 = lang_stars.idxmax()

users_df['leader_strength'] = users_df['followers'] / (1 + users_df['following'])
top_leaders = users_df.nlargest(5, 'leader_strength')['login'].tolist()
q8 = ','.join(top_leaders)

q9 = f"{users_df['followers'].corr(users_df['public_repos']):.3f}"

from sklearn.linear_model import LinearRegression
X = users_df['public_repos'].values.reshape(-1, 1)
y = users_df['followers'].values
reg = LinearRegression().fit(X, y)
q10 = f"{reg.coef_[0]:.3f}"

repos_df['has_projects'] = repos_df['has_projects'].fillna('false').astype(str).str.lower()
repos_df['has_wiki'] = repos_df['has_wiki'].fillna('false').astype(str).str.lower()

repos_df['has_projects_num'] = repos_df['has_projects'].apply(lambda x: 1 if x == 'true' else 0)
repos_df['has_wiki_num'] = repos_df['has_wiki'].apply(lambda x: 1 if x == 'true' else 0)

q11 = f"{repos_df['has_projects_num'].corr(repos_df['has_wiki_num']):.3f}"


hireable_following = users_df[users_df['hireable'] == 'true']['following'].mean()
non_hireable_following = users_df[users_df['hireable'] != 'true']['following'].mean()
q12 = f"{hireable_following - non_hireable_following:.3f}"

users_df['bio_words'] = users_df['bio'].fillna('').str.split().str.len()
bio_users = users_df[users_df['bio_words'] > 0]
X = bio_users['bio_words'].values.reshape(-1, 1)
y = bio_users['followers'].values
reg = LinearRegression().fit(X, y)
q13 = f"{reg.coef_[0]:.3f}"

repos_df['is_weekend'] = repos_df['created_at'].dt.dayofweek.isin([5, 6])
weekend_repos = repos_df[repos_df['is_weekend']].groupby('login').size()
top_weekend = weekend_repos.nlargest(5).index.tolist()
q14 = ','.join(top_weekend)

hireable_email = (users_df[users_df['hireable'] == 'true']['email'].notna().mean())
non_hireable_email = (users_df[users_df['hireable'] != 'true']['email'].notna().mean())
q15 = f"{hireable_email - non_hireable_email:.3f}"

def get_surname(name):
    if pd.isna(name): return None
    parts = str(name).strip().split()
    return parts[-1] if parts else None

users_df['surname'] = users_df['name'].apply(get_surname)
surname_counts = users_df['surname'].value_counts()
max_count = surname_counts.max()
most_common = sorted(surname_counts[surname_counts == max_count].index.tolist())
q16 = ','.join(most_common)

output = f"""Basel GitHub Users Analysis

1. Top 5 users by followers:
{q1}

2. 5 earliest registered users:
{q2}

3. Top 3 licenses:
{q3}

4. Most common company:
{q4}

5. Most popular language:
{q5}

6. Second most popular language for users after 2020:
{q6}

7. Language with highest average stars:
{q7}

8. Top 5 users by leader strength:
{q8}

9. Correlation between followers and public repos:
{q9}

10. Additional followers per public repository:
{q10}

11. Correlation between projects and wiki enabled:
{q11}

12. Difference in following count for hireable users:
{q12}

13. Impact of bio length on followers:
{q13}

14. Top 5 weekend repository creators:
{q14}

15. Difference in email sharing for hireable users:
{q15}

16. Most common surname(s):
{q16}
"""

# Save to file
with open('basel_github_analysis.txt', 'w') as f:
    f.write(output)