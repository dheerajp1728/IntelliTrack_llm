import requests
import base64
import hashlib
from typing import List, Dict, Optional
from qdrant_indexer import QdrantIndexer
import numpy as np

def get_github_files_and_hashes(repo_url: str, token: Optional[str] = None) -> List[Dict]:
    # Returns list of dicts: {file_path, commit_hash, content}
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
    result = []
    for file_path in files:
        if not file_path.endswith(('.py', '.cpp', '.h', '.js', '.ts', '.sh', '.html', '.md')):
            continue
        file_api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        file_resp = requests.get(file_api_url, headers=headers)
        if file_resp.status_code == 200:
            file_json = file_resp.json()
            if file_json.get('encoding') == 'base64':
                try:
                    content = base64.b64decode(file_json['content']).decode('utf-8', errors='ignore')
                    commit_hash = file_json.get('sha', '')
                    result.append({
                        "file_path": file_path,
                        "commit_hash": commit_hash,
                        "content": content
                    })
                except Exception:
                    continue
    return result

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    # Simple line-based chunking
    lines = text.splitlines()
    chunks = []
    i = 0
    while i < len(lines):
        chunk = '\n'.join(lines[i:i+chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def lmstudio_embed(text: str, model: str = "text-embedding-nomic-embed-text-v1.5") -> list:
    import requests
    import os
    clean_text = text[:80].replace('\n', ' ')
    print(f"[DEBUG] Embedding text (first 80 chars): {clean_text} ...")
    lm_studio_url = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234")
    payload = {
        "model": model,
        "input": [text]
    }
    response = requests.post(f"{lm_studio_url}/v1/embeddings", json=payload, timeout=30)
    response.raise_for_status()
    emb = response.json()["data"][0]["embedding"]
    print(f"[DEBUG] Got embedding of length {len(emb)}")
    return emb

def sync_repo_to_qdrant(repo_url: str, token: Optional[str], qdrant: QdrantIndexer):
    print(f"[DEBUG] Fetching files and hashes from repo: {repo_url}")
    files = get_github_files_and_hashes(repo_url, token)
    print(f"[DEBUG] Found {len(files)} code files to index.")
    for file in files:
        print(f"[DEBUG] Indexing file: {file['file_path']} (commit {file['commit_hash']})")
        chunks = chunk_text(file['content'])
        print(f"[DEBUG] File split into {len(chunks)} chunks.")
        for idx, chunk in enumerate(chunks):
            embedding = lmstudio_embed(chunk)
            print(f"[DEBUG] Upserting chunk {idx} of file {file['file_path']} to Qdrant.")
            qdrant.upsert_code_chunks([{
                "file_path": file['file_path'],
                "commit_hash": file['commit_hash'],
                "chunk_id": idx,
                "text": chunk,
                "embedding": embedding
            }])
    # TODO: Remove deleted files from Qdrant (not shown here)

def get_relevant_code_for_tasks(tasks: List[str], qdrant: QdrantIndexer, top_k=5) -> List[str]:
    code_blocks = []
    for task in tasks:
        print(f"[DEBUG] Embedding and searching for task: {task}")
        emb = lmstudio_embed(task)
        results = qdrant.search(emb, top_k=top_k)
        print(f"[DEBUG] Found {len(results)} relevant code chunks for task.")
        for r in results:
            code_blocks.append(r.payload['text'])
    return code_blocks
