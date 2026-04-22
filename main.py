from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests
import os
import re

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

def analyze_task_progress(task: str, commit_messages: List[str]) -> str:
    """Analyze task progress based on commit messages"""
    stopwords = {"with", "from", "that", "this", "have", "been", "will", "for", "the", "and", "not", 
        "add", "make", "more", "than", "into", "only", "also", "are", "all", "but", "can", 
        "has", "was", "use", "using", "able", "each", "per", "now", "new", "set", "get", 
        "put", "let", "out", "our", "your", "their", "about", "over", "such", "very", 
        "some", "just", "like", "done", "fix", "test", "file", "code", "repo", "main", 
        "step", "task", "docs", "doc", "readme"}
    
    keywords = [w.lower() for w in re.findall(r'\w+', task) 
        if len(w) > 3 and w.lower() not in stopwords]
    
    if not keywords:
        keywords = [w.lower() for w in re.findall(r'\w+', task)]
    
    completed_count = 0
    in_progress_count = 0
    
    for msg in commit_messages:
        msg_lower = msg.lower()
        if any(kw in msg_lower for kw in keywords):
            if any(word in msg_lower for word in ["done", "complete", "finished", "close", "resolved", "fixed"]):
                completed_count += 1
            else:
                in_progress_count += 1
    
    if completed_count > 0:
        return "done - commits found"
    elif in_progress_count > 0:
        return "in progress - work in commits"
    else:
        all_commits = " ".join(commit_messages).lower()
        for kw in keywords:
            if kw in all_commits:
                return "in progress - mentioned in history"
        return "not started - no references found"

@app.post("/progress", response_model=ProgressResponse)
def get_progress(data: ProgressRequest):
    """Analyze repository progress without Qdrant/Ollama"""
    try:
        print("\n" + "="*70, flush=True)
        print("📊 SIMPLIFIED PROGRESS ANALYSIS", flush=True)
        print("="*70, flush=True)
        print(f"Repository: {data.repo_url}", flush=True)
        
        # Step 1: Check GitHub Access
        print("\n[STEP 1] 🔍 Checking GitHub repository access...", flush=True)
        if not check_github_access(data.repo_url, data.github_token):
            raise HTTPException(status_code=400, detail="Cannot access repository. Check URL or token.")
        print("✅ Repository access verified", flush=True)
        
        # Step 2: Get Recent Commits
        print("\n[STEP 2] 📥 Fetching recent commits...", flush=True)
        commits = get_recent_commits(data.repo_url, data.github_token)
        if commits:
            print(f"✅ Retrieved {len(commits)} recent commits", flush=True)
            for i, commit in enumerate(commits[:3], 1):
                preview = commit[:60] if len(commit) > 60 else commit
                print(f"   {i}. {preview}...", flush=True)
        else:
            print("⚠️  No commits found", flush=True)
        
        # Step 3: Parse Tasks
        print("\n[STEP 3] 📋 Parsing task list...", flush=True)
        tasks = [t.strip() for t in data.tasks.replace(';', '\n').splitlines() if t.strip()]
        print(f"✅ Found {len(tasks)} tasks:", flush=True)
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task}", flush=True)
        
        # Step 4: Analyze Each Task
        print("\n[STEP 4] 🔎 Analyzing task progress...", flush=True)
        results = []
        for task in tasks:
            progress = analyze_task_progress(task, commits)
            results.append(TaskProgress(task=task, progress=progress))
            print(f"   ✓ {task}: {progress}", flush=True)
        
        # Calculate overall progress
        completed = sum(1 for r in results if "done" in r.progress.lower())
        progress_percent = int((completed / len(results) * 100) if results else 0)
        
        print("\n" + "="*70, flush=True)
        print(f"📈 Overall Progress: {progress_percent}%", flush=True)
        print("="*70 + "\n", flush=True)
        
        return ProgressResponse(results=results, progress_percent=progress_percent)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# To run: uvicorn main:app --reload
