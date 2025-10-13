from github import Github, Auth
import yaml

# ---------------------------
# Setup
# ---------------------------
# Load config from config.yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

token = config.get('github', {}).get("token")
if not token:
    raise ValueError("Please set the github_token in config.yaml")

g = Github(auth=Auth.Token(token))

# Read repo details from config
repo_name = config.get('github', {}).get('repo_name')
username = config.get('github', {}).get("username")
base_branch = config.get('github', {}).get("base_branch")
file_path = config.get('github', {}).get("file_path")
commit_message = config.get('github', {}).get("commit_message")
pr_title = config.get('github', {}).get("pr_title")

repo = g.get_repo(repo_name)

def get_next_branch_name():
    prs = repo.get_pulls(state="all", sort="created", direction="desc")
    next_pr_number = 1 if prs.totalCount == 0 else prs[0].number + 1
    return f"{username}_{next_pr_number}"

def create_new_branch():
    branch_name = get_next_branch_name()
    source = repo.get_branch(base_branch)
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)
    return branch_name
    
def commit_changes(branch_name):
    with open(file_path, "r") as f:
        content = f.read()

    # If file exists, update; else create
    try:
        contents = repo.get_contents(file_path, ref=branch_name)
        repo.update_file(contents.path, commit_message, content, contents.sha, branch=branch_name)
    except Exception:
        repo.create_file(file_path, commit_message, content, branch=branch_name)


def create_pull_request():
    branch_name=create_new_branch()
    commit_changes(branch_name)
    pr = repo.create_pull(
        title=pr_title,
        body="This PR was generated automatically.",
        head=branch_name,
        base=base_branch
    )
    print(f"Pull request created: {pr.html_url}")
    return pr.html_url



