import getpass
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

import orjson
import requests
from tqdm import tqdm

# GitHub Personal Access Token
if "GITHUB_TOKEN" not in os.environ:
    os.environ["GITHUB_TOKEN"] = getpass.getpass("Provide your Github Token Key")
token = os.environ["GITHUB_TOKEN"]

# GitHub 사용자명
if "GITHUB_USERNAME" not in os.environ:
    os.environ["GITHUB_USERNAME"] = getpass.getpass("Provide your Google API Key")
username = os.environ["GITHUB_USERNAME"]


def get_codes(row: Dict):
    repo = row["repo"]
    url = f"https://api.github.com/repos/{repo}/languages"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = response.json()
        row["codes"] = res
    return row


url = f"https://api.github.com/users/{username}/starred"
headers = {"Authorization": f"token {token}"}
rows = []

while url:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = response.json()
        rows.extend(res)
        url = None
        if "Link" in response.headers:
            links = response.headers["Link"].split(", ")
            for link in links:
                if 'rel="next"' in link:
                    url = link.split("; ")[0][1:-1]
    else:
        print(f"Failed to fetch starred repositories: {response.status_code}")
        break

for i, row in tqdm(enumerate(rows), total=len(rows)):
    rows[i] = {
        "url": row["html_url"],
        "description": row["description"],
        "topics": row["topics"],
        "repo": row["full_name"],
    }


result = []

with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    futures = {executor.submit(get_codes, row): row for row in rows}

    for future in tqdm(as_completed(futures), total=len(futures)):
        result.append(future.result())


with open("my_repo.json", "w", encoding="utf-8") as f:
    f.write(orjson.dumps(result, option=orjson.OPT_INDENT_2).decode("utf-8"))
