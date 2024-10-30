import requests
import pandas as pd
from time import sleep

# Replace with your token here
TOKEN = "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"
HEADERS = {"Authorization": f"token {TOKEN}"}

# Step 1: Fetch users in Basel with more than 10 followers
def fetch_users():
    url = "https://api.github.com/search/users"
    params = {"q": "location:Basel followers:>10", "per_page": 100, "page": 1}
    users = []

    while True:
        response = requests.get(url, headers=HEADERS, params=params).json()
        users.extend(response.get("items", []))
        if "next" not in response.get("links", {}):
            break  # Exit loop when no more pages
        params["page"] += 1
        sleep(2)  # Avoid hitting rate limits

    return users

# Step 2: Clean up the company field
def clean_company(company):
    if company:
        return company.strip().lstrip("@").upper()
    return ""

# Step 3: Fetch user details
def get_user_details(user):
    url = f"https://api.github.com/users/{user['login']}"
    response = requests.get(url, headers=HEADERS).json()
    return {
        "login": user["login"],
        "name": response.get("name", ""),
        "company": clean_company(response.get("company", "")),
        "location": response.get("location", ""),
        "email": response.get("email", ""),
        "hireable": response.get("hireable", ""),
        "bio": response.get("bio", ""),
        "public_repos": response.get("public_repos", 0),
        "followers": response.get("followers", 0),
        "following": response.get("following", 0),
        "created_at": response.get("created_at", ""),
    }

# Step 4: Main function to save data into CSV
def main():
    users = fetch_users()
    detailed_users = [get_user_details(user) for user in users]
    df = pd.DataFrame(detailed_users)
    df.to_csv("users.csv", index=False)

if __name__ == "__main__":
    main()
