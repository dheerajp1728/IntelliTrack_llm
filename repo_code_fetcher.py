import requests
import base64

def get_repo_files_and_code(repo_url: str, token: Optional[str]) -> List[str]:
    # Extract owner/repo from URL
    try:
        parts = repo_url.rstrip('/').split('/')
        owner, repo = parts[-2], parts[-1]
    except Exception:
        return []
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    resp = requests.get(api_url, headers=headers)
    if resp.status_code != 200:
        return []
    files = [item['path'] for item in resp.json().get('tree', []) if item['type'] == 'blob']
    code_snippets = []
    for file_path in files:
        if not file_path.endswith(('.py', '.cpp', '.h', '.js', '.ts', '.sh', '.html', '.md')):
            continue
        file_api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        file_resp = requests.get(file_api_url, headers=headers)
        if file_resp.status_code == 200:
            file_json = file_resp.json()
            if file_json.get('encoding') == 'base64':
                try:
                    code = base64.b64decode(file_json['content']).decode('utf-8', errors='ignore')
                    code_snippets.append(code)
                except Exception:
                    continue
    return code_snippets
