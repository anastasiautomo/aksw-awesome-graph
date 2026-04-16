import requests
from collections import defaultdict

API_URL = "https://api.github.com/orgs/AKSW/repos?per_page=60"
OUTPUT_FILE = "README.md"

HEADERS = {
    "Accept": "application/vnd.github.mercy-preview+json"
}


def fetch_repos():
    repos = []
    url = API_URL

    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        repos.extend(data)

        # pagination
        url = response.links.get("next", {}).get("url")

    return repos


def group_by_topics(repos):
    categories = defaultdict(list)

    for repo in repos:
        name = repo["name"]
        url = repo["html_url"]
        desc = repo["description"] or "No description available"
        topics = repo.get("topics", [])

        entry = f"- [{name}]({url}) - {desc}"

        if topics:
            for topic in topics:
                categories[topic.lower()].append(entry)
        else:
            categories["other"].append(entry)

    return categories


def generate_readme(categories):
    lines = []

    # Title
    lines.append("# AKSW Projects\n")
    lines.append("A list of projects from AKSW grouped by GitHub topics.\n")

    # Contents section (IMPORTANT for your parser)
    lines.append("## Contents\n")

    for category in sorted(categories.keys()):
        anchor = category.replace(" ", "-")
        lines.append(f"- [{category}](#{anchor})")

    # Category sections
    for category in sorted(categories.keys()):
        lines.append(f"\n## {category}\n")

        for item in categories[category]:
            lines.append(item)

    return "\n".join(lines)


def main():
    repos = fetch_repos()
    categories = group_by_topics(repos)
    readme_content = generate_readme(categories)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print(f"README.md generated with {len(repos)} repositories.")


if __name__ == "__main__":
    main()