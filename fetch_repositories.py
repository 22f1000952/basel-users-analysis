import requests
import pandas as pd
from time import sleep

# Token and Headers
TOKEN = "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"
HEADERS = {"Authorization": f"token {TOKEN}"}

# Step 1: Fetch repositories of a user
def fetch_repositories(user_login):
    url = f"https://api.github.com/users/{user_login}/repos"
    params = {"sort": "pushed", "per_page": 100, "page": 1}
    repos = []

    while True:
        response = requests.get(url, headers=HEADERS, params=params).json()
        if isinstance(response, dict) and "message" in response:
            print(f"Error: {response['message']} for {user_login}")
            break
        repos.extend(response)
        if len(response) < 100:
            break
        params["page"] += 1
        sleep(2)

    return repos

# Step 2: Save repositories data to CSV
def main():
    users = pd.read_csv("users.csv")["login"]
    all_repos = []

    for user in users:
        repos = fetch_repositories(user)
        for repo in repos:
            all_repos.append({
                "login": repo["owner"]["login"],
                "full_name": repo["full_name"],
                "created_at": repo["created_at"],
                "stargazers_count": repo["stargazers_count"],
                "watchers_count": repo["watchers_count"],
                "language": repo.get("language", ""),
                "has_projects": repo["has_projects"],
                "has_wiki": repo["has_wiki"],
                "license_name": repo["license"]["key"] if repo["license"] else "",
            })

    df = pd.DataFrame(all_repos)
    df.to_csv("repositories.csv", index=False)

if __name__ == "__main__":
    main()
