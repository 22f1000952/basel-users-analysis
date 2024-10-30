import requests
import pandas as pd
import time
from datetime import datetime
import os
from typing import List, Dict, Any
import logging
import sys
os.environ['GITHUB_TOKEN'] = 'your_token'
class GitHubScraper:
    def __init__(self, token: str):
        self.token = token.strip().strip("'").strip('"')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Verify token on initialization
        self.verify_token()

    def verify_token(self) -> bool:
        """Verify that the GitHub token is valid."""
        response = requests.get(f'{self.base_url}/user', headers=self.headers)

        if response.status_code == 401:
            self.logger.error("Invalid GitHub token. Please check your token and try again.")
            raise ValueError("Invalid GitHub token")

        if response.status_code != 200:
            self.logger.error(f"GitHub API error: {response.status_code}")
            raise ValueError("GitHub API error")

        user_data = response.json()
        self.logger.info(f"Authenticated as: {user_data.get('login')}")
        self.logger.info(f"Rate limit remaining: {response.headers.get('X-RateLimit-Remaining', 'unknown')}")
        return True

    def get_basel_users(self, min_followers: int = 10) -> List[Dict[str, Any]]:
        """Fetch GitHub users from Basel with more than specified followers."""
        users = []
        page = 1
        location_queries = ['Basel']

        for location in location_queries:
            self.logger.info(f"Searching for users in: {location}")

            while True:
                query = f'location:"{location}" followers:>{min_followers}'
                self.logger.info(f"Query: {query}, Page: {page}")

                response = requests.get(
                    f'{self.base_url}/search/users',
                    headers=self.headers,
                    params={'q': query, 'page': page, 'per_page': 100}
                )

                if response.status_code != 200:
                    self.logger.error(f"Error: {response.status_code}, {response.text}")
                    break

                data = response.json()
                self.logger.info(f"Found {len(data.get('items', []))} users on page {page}")

                if not data.get('items'):
                    break

                for user in data['items']:
                    if not any(existing_user.get('login') == user['login'] for existing_user in users):
                        user_details = self.get_user_details(user['login'])
                        if user_details:
                            user_location = user_details.get('location', '').lower()
                            if 'basel' in user_location:
                                users.append(user_details)
                                self.logger.info(f"Added user: {user['login']} ({user_details.get('location')})")

                    time.sleep(1)

                if len(data['items']) < 100:
                    break

                page += 1
            page = 1

        self.logger.info(f"Total unique Basel users found: {len(users)}")
        return users

    def get_user_details(self, username: str) -> Dict[str, Any]:
        """Fetch detailed information for a specific user."""
        self.logger.info(f"Fetching details for user: {username}")
        response = requests.get(f'{self.base_url}/users/{username}', headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"Error fetching user {username}: {response.status_code}")
            return None

    def get_user_repositories(self, username: str, max_repos: int = 500) -> List[Dict[str, Any]]:
        """Fetch repositories for a specific user."""
        self.logger.info(f"Fetching repositories for user: {username}")
        repos = []
        page = 1

        while len(repos) < max_repos:
            response = requests.get(
                f'{self.base_url}/users/{username}/repos',
                headers=self.headers,
                params={'sort': 'pushed', 'direction': 'desc', 'page': page, 'per_page': 100}
            )

            if response.status_code != 200:
                self.logger.error(f"Error fetching repos for {username}: {response.status_code}")
                break

            data = response.json()
            if not data:
                break

            repos.extend(data)
            self.logger.info(f"Fetched {len(data)} repositories for {username} (page {page})")

            if len(data) < 100:
                break

            page += 1
            time.sleep(1)

        return repos[:max_repos]

    def clean_company_name(self, company: str) -> str:
        """Clean company name according to specifications."""
        if not company:
            return ""
        company = company.strip()
        if company.startswith('@'):
            company = company[1:]
        return company.upper()

    def create_users_dataframe(self, users: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create users DataFrame."""
        user_data = [
            {
                'login': user.get('login', ''),
                'name': user.get('name', ''),
                'company': self.clean_company_name(user.get('company', '')),
                'location': user.get('location', ''),
                'email': user.get('email', ''),
                'hireable': str(user.get('hireable', '')).lower(),
                'bio': user.get('bio', ''),
                'public_repos': user.get('public_repos', 0),
                'followers': user.get('followers', 0),
                'following': user.get('following', 0),
                'created_at': user.get('created_at', '')
            }
            for user in users
        ]
        return pd.DataFrame(user_data)

    def create_repositories_dataframe(self, users: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create repositories DataFrame."""
        repo_data = []
        for user in users:
            repos = self.get_user_repositories(user['login'])
            for repo in repos:
                try:
                    license_name = repo.get('license', {}).get('key', '') if repo.get('license') else ''
                except AttributeError:
                    license_name = ''
                    self.logger.error(f"License data missing for {repo.get('full_name', '')}")

                repo_data.append({
                    'login': user['login'],
                    'full_name': repo.get('full_name', ''),
                    'created_at': repo.get('created_at', ''),
                    'stargazers_count': repo.get('stargazers_count', 0),
                    'watchers_count': repo.get('watchers_count', 0),
                    'language': repo.get('language', ''),
                    'has_projects': str(repo.get('has_projects', '')).lower(),
                    'has_wiki': str(repo.get('has_wiki', '')).lower(),
                    'license_name': license_name
                })
        return pd.DataFrame(repo_data)

def validate_token(token: str) -> str:
    """Validate and clean the GitHub token."""
    if not token:
        print("ERROR: GitHub token not found!")
        sys.exit(1)

    token = token.strip().strip("'").strip('"')
    if not token.startswith(('ghp_', 'github_pat_')):
        print("WARNING: Token format is incorrect.")
    return token

def main():
    token = validate_token(os.getenv('GITHUB_TOKEN'))

    try:
        scraper = GitHubScraper(token)
        users = scraper.get_basel_users(min_followers=10)

        if not users:
            print("No users found.")
            return

        users_df = scraper.create_users_dataframe(users)
        repos_df = scraper.create_repositories_dataframe(users)

        users_df.to_csv('users.csv', index=False)
        repos_df.to_csv('repositories.csv', index=False)

        print(f"Total users: {len(users_df)}")
        print(f"Total repositories: {len(repos_df)}")
        print(users_df.nlargest(5, 'followers')[['login', 'followers', 'public_repos']])

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
