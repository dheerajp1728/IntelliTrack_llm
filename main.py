from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import re
from llm_analyzer import LLMAnalyzer
from qdrant_indexer import QdrantIndexer
from code_indexer import sync_repo_to_qdrant, get_relevant_code_for_tasks
import requests
import os

app = FastAPI(title="IntelliTrack LLM Service")

# Add CORS middleware for Render deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProgressRequest(BaseModel):
    repo_url: str
    github_token: Optional[str] = None
    tasks: str

class TaskProgress(BaseModel):
    task: str
    progress: str

class ProgressResponse(BaseModel):
    results: List[TaskProgress]
    progress_percent: int


# ─── Health Check Endpoint ────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "IntelliTrack LLM Service"}


@app.get("/")
def root():
    return {"message": "IntelliTrack LLM Service is running", "docs_url": "/docs"}


# ─── Helper Functions ────────────────────────────────────────────────
def check_github_access(repo_url: str, token: Optional[str]) -> bool:
    # Extract owner/repo from URL
    try:
        parts = repo_url.rstrip('/').split('/')
        owner, repo = parts[-2], parts[-1]
    except Exception:
        return False
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    resp = requests.get(api_url, headers=headers)
    return resp.status_code == 200

def get_recent_commits(repo_url: str, token: Optional[str]) -> List[str]:
    try:
        parts = repo_url.rstrip('/').split('/')
        owner, repo = parts[-2], parts[-1]
    except Exception:
        return []
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    resp = requests.get(api_url, headers=headers)
    if resp.status_code == 200:
        return [commit["commit"]["message"] for commit in resp.json()]
    return []

def analyze_task_progress(task: str, commit_messages: List[str], code_snippets: List[str]) -> str:
    # Extract keywords (words longer than 3 chars, ignore common stopwords)
    stopwords = {"with", "from", "that", "this", "have", "been", "will", "for", "the", "and", "not", "add", "make", "more", "than", "into", "only", "also", "are", "all", "but", "can", "has", "was", "use", "using", "able", "each", "per", "now", "new", "set", "get", "put", "let", "out", "our", "your", "their", "about", "over", "such", "very", "some", "just", "like", "done", "fix", "test", "file", "code", "repo", "main", "step", "task", "docs", "doc", "docs", "readme"}
    keywords = [w.lower() for w in re.findall(r'\w+', task) if len(w) > 3 and w.lower() not in stopwords]
    # Check commit messages
    for msg in commit_messages:
        msg_lower = msg.lower()
        if any(kw in msg_lower for kw in keywords):
            if any(word in msg_lower for word in ["done", "complete", "finished", "close"]):
                return "done"
            return "in progress"
    # Check code content
    for code in code_snippets:
        code_lower = code.lower()
        if any(kw in code_lower for kw in keywords):
            return "in progress"
    return "not started"

@app.post("/progress", response_model=ProgressResponse)
def get_progress(data: ProgressRequest):
    import time
    try:
        start_time = time.time()
        
        print("\n" + "="*70, flush=True)
        print("📊 PROGRESS ANALYSIS REQUEST STARTED", flush=True)
        print("="*70, flush=True)
        print(f"Repository: {data.repo_url}", flush=True)
        print(f"GitHub Token: {'Yes' if data.github_token else 'No'}", flush=True)
        
        # Step 1: Check GitHub Access
        print("\n[STEP 1/7] 🔍 Checking GitHub repository access...", flush=True)
        if not check_github_access(data.repo_url, data.github_token):
            raise HTTPException(status_code=400, detail="Cannot access repository. Check URL or token.")
        print("✅ Repository access verified", flush=True)
        
        # Step 2: Initialize Qdrant
        print("\n[STEP 2/7] 🗄️  Initializing Qdrant vector database...", flush=True)
        qdrant = QdrantIndexer()
        print("✅ Qdrant initialized", flush=True)
        
        # Step 3: Sync Repository
        print("\n[STEP 3/7] 📥 Fetching and indexing repository code...", flush=True)
        sync_repo_to_qdrant(data.repo_url, data.github_token, qdrant)
        elapsed = time.time() - start_time
        print(f"✅ Repository indexed successfully ({elapsed:.1f}s elapsed)", flush=True)
        
        # Step 4: Parse Tasks
        print("\n[STEP 4/7] 📋 Parsing task list...", flush=True)
        tasks = [t.strip() for t in data.tasks.replace(';', '\n').splitlines() if t.strip()]
        print(f"✅ Found {len(tasks)} tasks:", flush=True)
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task}", flush=True)
        
        # Step 5: Search for Relevant Code
        print("\n[STEP 5/7] 🔎 Searching for relevant code in repository...", flush=True)
        code_blocks = get_relevant_code_for_tasks(tasks, qdrant, top_k=5)
        elapsed = time.time() - start_time
        print(f"✅ Retrieved {len(code_blocks)} code blocks ({elapsed:.1f}s elapsed)", flush=True)
        
        # Step 6: LLM Analysis
        print("\n[STEP 6/7] 🤖 Analyzing with LLM (this may take 30-60 seconds)...", flush=True)
        print("   ⏳ Waiting for LLM response...", flush=True)
        llm = LLMAnalyzer()
        llm_start = time.time()
        progress_summaries, percent_done = llm.analyze_tasks_with_summary(code_blocks, tasks)
        llm_elapsed = time.time() - llm_start
        print(f"✅ LLM analysis complete ({llm_elapsed:.1f}s)", flush=True)
        
        # Step 7: Format Results
        print("\n[STEP 7/7] 📦 Formatting results...", flush=True)
        results = [TaskProgress(task=task, progress=summary) for task, summary in zip(tasks, progress_summaries)]
        print("✅ Results formatted", flush=True)
        
        # Final Summary
        total_elapsed = time.time() - start_time
        print("\n" + "="*70, flush=True)
        print("✅ ANALYSIS COMPLETE", flush=True)
        print("="*70, flush=True)
        print(f"📈 Overall Progress: {percent_done}%", flush=True)
        print(f"⏱️  Total Time: {total_elapsed:.1f}s", flush=True)
        print(f"   - GitHub/Qdrant: {elapsed - llm_elapsed:.1f}s", flush=True)
        print(f"   - LLM Analysis:   {llm_elapsed:.1f}s", flush=True)
        print(f"📊 Results:", flush=True)
        for i, (task, summary) in enumerate(zip(tasks, progress_summaries), 1):
            print(f"   {i}. {task}", flush=True)
            print(f"      └─ {summary}", flush=True)
        print("="*70 + "\n", flush=True)
        
        return {"results": results, "progress_percent": percent_done}
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ [ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# To run: uvicorn main:app --reload
