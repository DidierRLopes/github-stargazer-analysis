import argparse
import csv
import glob
import json
import os
import shutil
from datetime import datetime
from time import sleep

import pandas as pd
import requests


def setup_folder(repo_owner, repo_name):
    """
    Create folder and get the latest CSV file if it exists.
    """
    folder_name = f"{repo_owner}_{repo_name}"
    os.makedirs(folder_name, exist_ok=True)

    list_of_files = glob.glob(
        os.path.join(folder_name, "stargazer_info_*.csv")
    )
    latest_file = (
        max(list_of_files, key=os.path.getctime) if list_of_files else None
    )

    return folder_name, latest_file


def get_latest_stargazer_data(latest_file):
    """
    Extract latest starred date and number of stargazers from existing CSV.
    """
    if latest_file:
        df = pd.read_csv(latest_file)
        return df["Starred at"].max(), len(df)
    return None, 0


def save_stargazer_data(folder_name, latest_file, stargazer_info):
    """
    Save stargazer information to a CSV file.
    """
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = os.path.join(
        folder_name, f"stargazer_info_{current_datetime}.csv"
    )

    # Copy existing data if available
    if latest_file:
        shutil.copy(latest_file, csv_filename)

    # Append new data
    with open(csv_filename, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Username",
            "Name",
            "Location",
            "Company",
            "Email",
            "Twitter",
            "Followers",
            "Starred at",
            "Bio",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if os.path.getsize(csv_filename) == 0:
            writer.writeheader()

        for user in stargazer_info:
            writer.writerow(
                {
                    "Username": user["login"],
                    "Name": user["name"],
                    "Location": user["location"],
                    "Company": user["company"],
                    "Email": user["email"],
                    "Twitter": user["twitter_username"],
                    "Followers": user["followers"],
                    "Starred at": user["starred_at"],
                    "Bio": user["bio"],
                }
            )

    return csv_filename


def get_stargazers(owner, repo, token, latest_num_stargazers, limit=None):
    """
    Retrieve all stargazers for a given repository.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/stargazers"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.star+json",
    }
    stargazers = []

    page = (latest_num_stargazers // 30) + 1 if latest_num_stargazers else 1

    while True:
        try:
            print(f"Fetching page {page} of stargazers...")
            response = requests.get(f"{url}?page={page}", headers=headers)

            remaining_calls = int(
                response.headers.get("X-RateLimit-Remaining", 0)
            )
            if remaining_calls < 10:
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                sleep_time = (
                    max(reset_time - datetime.now().timestamp(), 0) + 10
                )
                print(
                    f"Rate limit nearly exceeded. Waiting {sleep_time:.0f} seconds..."
                )
                sleep(sleep_time)

            if response.status_code == 200:
                page_stargazers = response.json()
                if not page_stargazers:
                    break
                stargazers.extend(page_stargazers)

                print(f"DEBUG: Retrieved {len(stargazers)} stargazers so far")
                print(f"DEBUG: Limit is {limit}")
                print([stargazer["user"]["login"] for stargazer in stargazers])

                if limit and len(stargazers) >= limit:
                    break

                page += 1

            elif response.status_code == 403:
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                sleep_time = (
                    max(reset_time - datetime.now().timestamp(), 0) + 10
                )
                print(
                    f"Rate limit exceeded. Waiting {sleep_time:.0f} seconds..."
                )
                sleep(sleep_time)
            else:
                print(f"Error: Status code {response.status_code}")
                print(f"Response: {response.text}")
                break

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            sleep(5)

    return stargazers


def extract_stargazer_info(
    owner, repo, token, latest_starred_at, latest_num_stargazers, limit=None
):
    """
    Extract all information from GitHub profiles that stargaze a given project.
    """
    stargazers = get_stargazers(
        owner, repo, token, latest_num_stargazers, limit
    )

    detailed_stargazers = []
    new_users_count = 0

    for stargazer in stargazers:
        username = stargazer["user"]["login"]
        starred_at = stargazer["starred_at"]
        starred_at_datetime = datetime.strptime(
            starred_at, "%Y-%m-%dT%H:%M:%SZ"
        )
        latest_starred_at_datetime = (
            datetime.strptime(latest_starred_at, "%Y-%m-%dT%H:%M:%SZ")
            if latest_starred_at
            else None
        )

        if (
            latest_starred_at_datetime is None
            or starred_at_datetime > latest_starred_at_datetime
        ):
            if limit and new_users_count >= limit:
                break

            print(
                f"Processing stargazer #{latest_num_stargazers+new_users_count}: {username}"
            )
            user_response = requests.get(
                f"https://api.github.com/users/{username}",
                headers={"Authorization": f"token {token}"},
            )
            user_info = (
                user_response.json()
                if user_response.status_code == 200
                else None
            )

            if user_info:
                user_info["starred_at"] = starred_at
                detailed_stargazers.append(user_info)
                new_users_count += 1

            if int(user_response.headers.get("X-RateLimit-Remaining", 0)) < 10:
                sleep(60)
        else:
            print(f"Already processed stargazer {username}")

    return detailed_stargazers


def main():
    parser = argparse.ArgumentParser(description="Scrape GitHub stargazers")
    parser.add_argument("--token", required=True, help="GitHub API token")
    parser.add_argument("--owner", required=True, help="Repository owner")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of new stargazers to fetch",
    )

    args = parser.parse_args()

    folder_name, latest_file = setup_folder(args.owner, args.repo)
    latest_starred_at, latest_num_stargazers = get_latest_stargazer_data(
        latest_file
    )

    if latest_file:
        print(
            f"We have already processed {latest_num_stargazers} stargazers (until {latest_starred_at})"
        )

    if args.limit:
        print(f"We will now fetch the next {args.limit} stargazers")
    else:
        print("We will fetch the remaining stargazers")

    stargazer_info = extract_stargazer_info(
        args.owner,
        args.repo,
        args.token,
        latest_starred_at,
        latest_num_stargazers,
        limit=args.limit,
    )

    csv_filename = save_stargazer_data(
        folder_name, latest_file, stargazer_info
    )
    print(f"Data saved to {csv_filename}")

    df = pd.read_csv(csv_filename)
    print(df)


if __name__ == "__main__":
    main()
