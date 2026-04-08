#!/usr/bin/env python3
"""
Example: Using the Agile Tracker API

This script demonstrates how to use the /progress endpoint
to analyze project task completion status.
"""

import requests
import json
from typing import Dict, List

API_BASE_URL = "http://127.0.0.1:8004"

def analyze_project(repo_url: str, tasks: List[str], github_token: str = None) -> Dict:
    """
    Analyze a project and get task progress status.
    
    Args:
        repo_url: GitHub repository URL
        tasks: List of task descriptions
        github_token: Optional GitHub API token for private repos
        
    Returns:
        Dictionary containing results and overall progress_percent
    """
    # Prepare request
    payload = {
        "repo_url": repo_url,
        "tasks": "\n".join(tasks),
    }
    
    if github_token:
        payload["github_token"] = github_token
    
    # Make request
    print(f"📊 Analyzing project: {repo_url}")
    print(f"📋 Tasks to analyze: {len(tasks)}")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/progress",
            json=payload,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        return data
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (took more than 5 minutes)")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Is the API server running?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def print_results(data: Dict):
    """Pretty print the results"""
    if not data:
        return
    
    overall_progress = data.get("progress_percent", 0)
    results = data.get("results", [])
    
    print(f"\n✅ Analysis Complete!")
    print(f"📈 Overall Progress: {overall_progress}%")
    print("-" * 60)
    
    # Color-code by status
    status_colors = {
        "done": "✅",
        "in progress": "🔄",
        "not started": "⏳"
    }
    
    for i, result in enumerate(results, 1):
        task = result.get("task", "Unknown")
        progress = result.get("progress", "No status")
        
        # Extract status
        status = "unknown"
        if "[done]" in progress:
            status = "done"
        elif "[in progress]" in progress:
            status = "in progress"
        elif "[not started]" in progress:
            status = "not started"
        
        emoji = status_colors.get(status, "❓")
        
        print(f"\n{i}. {emoji} {task}")
        print(f"   └─ {progress}")

def example_search_engine():
    """Example: Analyze the Search Engine project"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Search Engine Project")
    print("="*60)
    
    repo_url = "https://github.com/vignesh362/Search-Engine"
    tasks = [
        "Implement BM25 ranking algorithm",
        "Build compressed inverted index with VarByte encoding",
        "Add support for both OR and AND query modes",
        "Create a Google-like web interface for search",
        "Enable real-time system logs in the UI",
        "Implement query-dependent snippet generation",
    ]
    
    data = analyze_project(repo_url, tasks)
    print_results(data)
    
    return data

def example_multiple_repos():
    """Example: Analyze multiple repositories"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Multiple Repositories")
    print("="*60)
    
    projects = [
        {
            "url": "https://github.com/vignesh362/Search-Engine",
            "tasks": ["Implement search", "Add web UI", "Optimize queries"]
        },
    ]
    
    results = {}
    for project in projects:
        print(f"\n📊 Analyzing: {project['url']}")
        data = analyze_project(project["url"], project["tasks"])
        results[project["url"]] = data
        print_results(data)
        print("-" * 60)
    
    # Summary
    print("\n📋 SUMMARY")
    print("=" * 60)
    for url, data in results.items():
        if data:
            progress = data.get("progress_percent", 0)
            print(f"  {url}: {progress}%")

def example_json_output():
    """Example: Get raw JSON output"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Raw JSON Output")
    print("="*60)
    
    repo_url = "https://github.com/vignesh362/Search-Engine"
    tasks = ["Implement BM25", "Build index"]
    
    data = analyze_project(repo_url, tasks)
    
    if data:
        print("\nRaw JSON Response:")
        print(json.dumps(data, indent=2))

def main():
    """Run examples"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + "Agile Tracker API - Usage Examples".center(58) + "║")
    print("╚" + "="*58 + "╝")
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=2)
        print("\n✅ API is running at", API_BASE_URL)
    except:
        print("\n❌ API is not running at", API_BASE_URL)
        print("Start it with: python -m uvicorn main:app --host 127.0.0.1 --port 8004")
        return
    
    # Run examples
    example_search_engine()
    
    # Uncomment to run other examples:
    # example_multiple_repos()
    # example_json_output()
    
    print("\n" + "="*60)
    print("✅ Examples completed!")
    print("="*60)

if __name__ == "__main__":
    main()
