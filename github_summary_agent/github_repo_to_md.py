import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

import orjson
from tqdm import tqdm


def process_url(row: Dict):
    url = row["url"]
    user_name = url.split("/")[-2]
    repo_name = url.split("/")[-1]
    cmd = f"clipper clip -u {url} -o output/{user_name}_{repo_name}.md"
    subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


with open("my_repo.json", mode="r", encoding="utf-8") as f:
    rows = orjson.loads(f.read())

with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    list(tqdm(executor.map(process_url, rows), total=len(rows)))
