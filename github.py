#!/usr/bin/env python
import requests
from pymongo import MongoClient
import pdb
import os

def update_github_status(repo_full, commit, state, description, target_url):
    token     = os.environ['GITHUB']

    url = "https://{}:x-oauth-basic@api.github.com/repos/{}/statuses/{}".format(token, repo_full, commit)
    print(url)

    status_data = {"state": state,
                   "target_url": target_url,
                   "description": description,
                   "context": "ci/next-prod"}

    print("Updating github: ", status_data)
    r = requests.post(url, json=status_data)

