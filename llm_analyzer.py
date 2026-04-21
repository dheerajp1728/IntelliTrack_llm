import requests
import json as pyjson
import re
import traceback
import os
from typing import List

class LLMAnalyzer:
    def __init__(self, api_url: str = None):
        if api_url is None:
            lm_studio_url = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234")
            api_url = f"{lm_studio_url}/v1/chat/completions"
        self.api_url = api_url

    def analyze_tasks_with_summary(self, repo_code: List[str], tasks: List[str]):
        """
        Given a list of code/doc strings and a list of tasks, return a tuple:
        (list of per-task summaries, overall percent as int)
        Each summary is a string like: "[status] - summary"
        """
        joined_code = "\n\n".join(repo_code)
        joined_tasks = "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
        
        # More explicit prompt format with better guidance
        prompt = f"""Analyze the provided code and determine implementation status for each task.

CODE CONTEXT:
{joined_code[:6000]}

TASKS TO ANALYZE:
{joined_tasks}

For each task, determine:
1. Status: done (fully implemented), in progress (partially done), or not started (no implementation)
2. Brief summary: 3-5 words describing what you found or didn't find

Respond with ONLY this JSON structure (no other text):
{{
  "overall_progress": 0-100,
  "tasks": [
    {{"status": "done", "summary": "What is implemented"}},
    {{"status": "in progress", "summary": "What's been partially added"}},
    {{"status": "not started", "summary": "Why it's not in code"}}
  ]
}}

Status values must be: done, in progress, or not started
Response MUST be valid JSON only.
"""
        
        payload = {
            "model": "llama-2-7b-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1024
        }
        
        try:
            print(f"[DEBUG] Sending analysis request to LLM at {self.api_url}...", flush=True)
            response = requests.post(self.api_url, json=payload, timeout=300)
            
            print(f"[DEBUG] LLM Response Status: {response.status_code}", flush=True)
            
            if response.status_code != 200:
                print(f"[ERROR] LLM API returned {response.status_code}: {response.text[:200]}", flush=True)
                return self._create_empty_response(tasks)
            
            result = response.json()
            
            if "choices" not in result or len(result["choices"]) == 0:
                print(f"[ERROR] Invalid LLM response format (no choices)", flush=True)
                return self._create_empty_response(tasks)
            
            content = result["choices"][0].get("message", {}).get("content", "")
            print(f"[DEBUG] LLM Response received ({len(content)} chars)", flush=True)
            print(f"[DEBUG] Content preview: {content[:200]}", flush=True)
            
            # Extract JSON from response
            match = re.search(r'\{[\s\S]*\}', content)
            if not match:
                print(f"[ERROR] Could not find JSON in LLM response", flush=True)
                print(f"[DEBUG] Full response: {content[:500]}", flush=True)
                return self._create_empty_response(tasks)
            
            try:
                data = pyjson.loads(match.group(0))
                print(f"[DEBUG] Successfully parsed JSON", flush=True)
            except pyjson.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse JSON: {e}", flush=True)
                return self._create_empty_response(tasks)
            
            if "tasks" not in data:
                print(f"[ERROR] Response missing 'tasks' field. Keys: {list(data.keys())}", flush=True)
                return self._create_empty_response(tasks)
            
            # Build summaries from response
            summaries = []
            response_tasks = data.get("tasks", [])
            
            if len(response_tasks) != len(tasks):
                print(f"[WARNING] Task count mismatch: expected {len(tasks)}, got {len(response_tasks)}", flush=True)
            
            for i, task in enumerate(tasks):
                if i < len(response_tasks):
                    task_result = response_tasks[i]
                    status = task_result.get("status", "not started").strip().lower()
                    summary = task_result.get("summary", "Analyzed").strip()
                    
                    # Validate status - allow variations
                    status_lower = status.replace(" ", "").lower()
                    if "done" in status_lower:
                        status = "done"
                    elif "progress" in status_lower:
                        status = "in progress"
                    elif "notstarted" in status_lower or "not-started" in status_lower:
                        status = "not started"
                    else:
                        print(f"[WARNING] Invalid status '{status}' for task {i+1}, using 'not started'", flush=True)
                        status = "not started"
                    
                    if not summary or summary.lower() == "":
                        summary = "Analyzed"
                    
                    summaries.append(f"[{status}] - {summary}")
                    print(f"[DEBUG] Task {i+1}: [{status}] - {summary}", flush=True)
                else:
                    summaries.append("[not started] - No analysis")
                    print(f"[DEBUG] Task {i+1}: missing from LLM response", flush=True)
            
            # Get overall progress percent
            percent = int(data.get("overall_progress", data.get("progress_percent", 0)))
            if percent < 0:
                percent = 0
            if percent > 100:
                percent = 100
            
            print(f"[DEBUG] LLM Analysis Complete: {percent}% overall", flush=True)
            
            return summaries, percent
            
        except requests.exceptions.Timeout:
            print(f"[ERROR] LLM request timed out after 300s", flush=True)
            return self._create_empty_response(tasks)
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Cannot connect to LLM at {self.api_url}", flush=True)
            return self._create_empty_response(tasks)
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}", flush=True)
            traceback.print_exc()
            return self._create_empty_response(tasks)
    
    def _create_empty_response(self, tasks: List[str]):
        """Return empty response when LLM fails"""
        return ([f"[not started] - No analysis available" for _ in tasks], 0)
