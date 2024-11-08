# GitHub Stargazer Analysis

A tool to analyze GitHub repository stargazers, providing insights into your community demographics including location, company, job roles, and more.

## Features

- Scrapes detailed information about users who have starred your repository
- Tracks star history over time
- Generates visualizations including:
  - Weekly star trends
  - Geographic distribution of stargazers
  - Top companies and job roles
  - Word clouds from user bios
  - Most influential stargazers by follower count
- Handles rate limiting automatically
- Incremental updates (only fetches new stargazers)

## Setup

### Prerequisites

- Python 3.11+
- Jupyter Notebook
- A GitHub Personal Access Token

### Installation

1. Clone the repository.

2. Install all required libraries

```
pip install pandas requests nltk wordcloud matplotlib seaborn plotly jupyter
```

3. Create a .env file with a GITHUB_TOKEN for scraping and an OPENAI_API_KEY for processing.

```
GITHUB_TOKEN=your_github_personal_access_token
OPENAI_API_KEY=your_github_personal_access_token
```

## Getting Started

This is divided in 3 different scripts.

### Stargazers scraping

You can either use the python script with:

```
scrape_stargazers.py --token $GITHUB_TOKEN --owner <repository-owner> --repo <repository-name>
```

or use the Jupyter notebook: `stargazers_scraping.ipynb`.

The script will create a folder named `<owner>_<repo>` containing a CSV file with stargazer information.

The information is:
- Username
- Name
- Location
- Company
- Email (if public)
- Twitter handle
- Follower count
- Star timestamp
- Bio

The script automatically handles GitHub API rate limiting by:
- Monitoring remaining API calls
- Pausing when approaching limits
- Resuming automatically when rate limits reset

Note: You can use the variable "LIMIT" to test with less stargazers than the total amount.

Note2: If you have already run the script once, re-running it will scrape to new stargazers.


### Stargazers processing

This processing uses OpenAI to:
- Extract user's location, company and job title from GitHub bio.
- Standardize location
  - "Lisbon" -> "Portugal, Lisbon"
  - "Brooklyn" -> "USA, New York"
- Standardize company name
  - "GOOGLE" -> "Google"
  - "Facebook" -> "Meta"

This was rather expensive as I was using `GPT-4o` since other models weren't good enough and I didn't want to spend too much time on this task.

If you have time I recommend iterating here to use another model, or even try to come up with an alternative to do spend less money on tokens.


### Stargazers analysis

Now that we have all of our dataset cleaned up, I just run analysis on that data.

Here are some examples of charts that get generated:
- Weekly Stars Over Time
- Stargazers by Major Regions
- Top Countries of Stargazers
- Top Region of Stargazers
- Top Company of Stargazers
- Top Job of Stargazers
- Stargazers by Job Category
- Top Job of Stargazers (Excluding Engineers & Developers)
- Top 20 Words in Stargazer Bios
- Top 30 Stargazers by Follower Count

Based on some preliminary analysis I found that some of the processing wasn't the best, so I do some further post-processing. Initially I had that in the previous notebook but since I was utilizing the charts generated in this notebook to iterate it was faster to do post-processing here.


## Final remarks

A lot more can be done here to automate this process, make it cheaper and/or faster.

But this got the job done in a few hours of work, which was ideal for me.

Feel free to create issues or PRs to the repo.

