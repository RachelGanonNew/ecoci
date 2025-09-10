"""
GitHub Tools for MCP Server

This module provides tools for interacting with the GitHub API through the MCP server.
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from github import Github, GithubIntegration, Auth
from github.Repository import Repository
from github.WorkflowRun import WorkflowRun
from github.PaginatedList import PaginatedList

from ....core.config import settings
from ....services.mcp_server import ToolDefinition
from ....schemas.mcp import ToolParameterSchema

logger = logging.getLogger(__name__)

# Tool Definitions
ANALYZE_REPO_TOOL = {
    "name": "github.analyze_repository",
    "description": "Analyze a GitHub repository for CI/CD inefficiencies",
    "parameters": {
        "owner": {"type": "string", "description": "Repository owner"},
        "repo": {"type": "string", "description": "Repository name"},
        "branch": {"type": "string", "description": "Branch to analyze", "default": "main"},
        "lookback_days": {"type": "integer", "description": "Number of days of workflow runs to analyze", "default": 30}
    },
    "required": ["owner", "repo"]
}

GET_WORKFLOW_RUNS_TOOL = {
    "name": "github.get_workflow_runs",
    "description": "Get workflow runs for a repository",
    "parameters": {
        "owner": {"type": "string", "description": "Repository owner"},
        "repo": {"type": "string", "description": "Repository name"},
        "branch": {"type": "string", "description": "Filter by branch"},
        "event": {"type": "string", "description": "Filter by event that triggered the workflow"},
        "status": {"type": "string", "description": "Filter by workflow run status", 
                    "enum": ["completed", "action_required", "cancelled", "failure", "neutral", "success", "skipped", "stale", "timed_out", "in_progress", "queued", "requested", "waiting"]},
        "per_page": {"type": "integer", "description": "Results per page", "default": 30, "maximum": 100},
        "page": {"type": "integer", "description": "Page number", "default": 1}
    },
    "required": ["owner", "repo"]
}

GET_WORKFLOW_RUN_LOGS_TOOL = {
    "name": "github.get_workflow_run_logs",
    "description": "Get logs for a specific workflow run",
    "parameters": {
        "owner": {"type": "string", "description": "Repository owner"},
        "repo": {"type": "string", "description": "Repository name"},
        "run_id": {"type": "integer", "description": "ID of the workflow run"}
    },
    "required": ["owner", "repo", "run_id"]
}

CREATE_ISSUE_TOOL = {
    "name": "github.create_issue",
    "description": "Create a new GitHub issue",
    "parameters": {
        "owner": {"type": "string", "description": "Repository owner"},
        "repo": {"type": "string", "description": "Repository name"},
        "title": {"type": "string", "description": "Issue title"},
        "body": {"type": "string", "description": "Issue body"},
        "labels": {"type": "array", "items": {"type": "string"}, "description": "Labels to apply to the issue"},
        "assignees": {"type": "array", "items": {"type": "string"}, "description": "Usernames to assign to the issue"}
    },
    "required": ["owner", "repo", "title"]
}

class GitHubTools:
    """GitHub tools for the MCP server."""
    
    def __init__(self):
        self.app_id = settings.GITHUB_APP_ID
        self.private_key = settings.GITHUB_APP_PRIVATE_KEY
        self.client = None
        self._integration = None
        self._installation_tokens = {}
    
    @property
    def integration(self):
        """Lazy-load the GitHub integration."""
        if self._integration is None:
            auth = Auth.AppAuth(self.app_id, self.private_key)
            self._integration = GithubIntegration(auth=auth)
        return self._integration
    
    async def get_installation_token(self, owner: str, repo: str) -> str:
        """Get an installation token for a repository."""
        cache_key = f"{owner}/{repo}"
        
        # Check if we have a valid cached token
        if cache_key in self._installation_tokens:
            token_data = self._installation_tokens[cache_key]
            if datetime.utcnow() < token_data["expires_at"] - timedelta(minutes=5):
                return token_data["token"]
        
        # Get a new installation token
        try:
            # Get installation ID for the repository
            installation = self.integration.get_installation(owner, repo)
            
            # Create installation access token
            auth = self.integration.get_access_token(installation.id)
            
            # Cache the token
            self._installation_tokens[cache_key] = {
                "token": auth.token,
                "expires_at": auth.expires_at
            }
            
            return auth.token
            
        except Exception as e:
            logger.error(f"Failed to get installation token: {str(e)}")
            raise Exception(f"Failed to authenticate with GitHub: {str(e)}")
    
    async def get_repository(self, owner: str, repo: str) -> Repository:
        """Get a GitHub repository client."""
        token = await self.get_installation_token(owner, repo)
        g = Github(token)
        return g.get_repo(f"{owner}/{repo}")
    
    async def analyze_repository(
        self, 
        owner: str, 
        repo: str, 
        branch: str = "main",
        lookback_days: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze a GitHub repository for CI/CD inefficiencies.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch to analyze (default: main)
            lookback_days: Number of days of workflow runs to analyze (default: 30)
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Get repository and workflow runs
            repository = await self.get_repository(owner, repo)
            since = datetime.utcnow() - timedelta(days=lookback_days)
            
            # Get workflow runs for the specified branch
            workflow_runs = repository.get_workflow_runs(
                branch=branch,
                created=f">={since.isoformat()}"
            )
            
            # Analyze workflow runs
            total_runs = workflow_runs.totalCount
            successful_runs = sum(1 for run in workflow_runs if run.conclusion == "success")
            failed_runs = sum(1 for run in workflow_runs if run.conclusion == "failure")
            cancelled_runs = sum(1 for run in workflow_runs if run.conclusion == "cancelled")
            
            # Calculate metrics
            success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
            
            # Calculate average duration
            durations = []
            for run in workflow_runs:
                if run.status == "completed" and run.created_at and run.updated_at:
                    duration = (run.updated_at - run.created_at).total_seconds()
                    durations.append(duration)
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Identify frequent failures
            workflows = {}
            for run in workflow_runs:
                if not run.workflow_id:
                    continue
                    
                workflow_name = run.name or f"Workflow {run.workflow_id}"
                if workflow_name not in workflows:
                    workflows[workflow_name] = {
                        "total_runs": 0,
                        "successful_runs": 0,
                        "failed_runs": 0,
                        "durations": []
                    }
                
                workflows[workflow_name]["total_runs"] += 1
                if run.conclusion == "success":
                    workflows[workflow_name]["successful_runs"] += 1
                elif run.conclusion == "failure":
                    workflows[workflow_name]["failed_runs"] += 1
                
                if run.status == "completed" and run.created_at and run.updated_at:
                    duration = (run.updated_at - run.created_at).total_seconds()
                    workflows[workflow_name]["durations"].append(duration)
            
            # Calculate workflow metrics
            workflow_metrics = []
            for name, data in workflows.items():
                if data["total_runs"] > 0:
                    success_rate = (data["successful_runs"] / data["total_runs"]) * 100
                    avg_duration = sum(data["durations"]) / len(data["durations"]) if data["durations"] else 0
                    
                    workflow_metrics.append({
                        "name": name,
                        "total_runs": data["total_runs"],
                        "success_rate": round(success_rate, 2),
                        "avg_duration_seconds": round(avg_duration, 2),
                        "failure_rate": round(100 - success_rate, 2)
                    })
            
            # Sort workflows by failure rate (highest first)
            workflow_metrics.sort(key=lambda x: x["failure_rate"], reverse=True)
            
            # Get repository languages
            try:
                languages = repository.get_languages()
            except Exception as e:
                logger.warning(f"Failed to get repository languages: {str(e)}")
                languages = {}
            
            # Generate recommendations
            recommendations = []
            
            # Check for long-running workflows
            for workflow in workflow_metrics:
                if workflow["avg_duration_seconds"] > 600:  # More than 10 minutes
                    recommendations.append({
                        "type": "performance",
                        "severity": "high",
                        "message": f"Workflow '{workflow['name']}' is slow (avg {workflow['avg_duration_seconds']:.1f}s)",
                        "suggestion": "Consider optimizing the workflow by caching dependencies, running jobs in parallel, or using matrix builds."
                    })
            
            # Check for flaky tests
            for workflow in workflow_metrics:
                if workflow["failure_rate"] > 20:  # More than 20% failure rate
                    recommendations.append({
                        "type": "reliability",
                        "severity": "critical" if workflow["failure_rate"] > 50 else "high",
                        "message": f"High failure rate in workflow '{workflow['name']}' ({workflow['failure_rate']:.1f}%)",
                        "suggestion": "Investigate test failures and add retry logic for flaky tests."
                    })
            
            # Check for outdated dependencies
            try:
                dependabot_alerts = repository.get_vulnerability_alert()
                if dependabot_alerts.totalCount > 0:
                    recommendations.append({
                        "type": "security",
                        "severity": "high",
                        "message": f"{dependabot_alerts.totalCount} security vulnerabilities found",
                        "suggestion": "Update dependencies to their latest secure versions using Dependabot or similar tools."
                    })
            except Exception as e:
                logger.warning(f"Failed to get vulnerability alerts: {str(e)}")
            
            # Generate summary
            summary = {
                "repository": f"{owner}/{repo}",
                "branch": branch,
                "analysis_period_days": lookback_days,
                "total_workflow_runs": total_runs,
                "success_rate_percent": round(success_rate, 2),
                "failed_runs": failed_runs,
                "cancelled_runs": cancelled_runs,
                "avg_workflow_duration_seconds": round(avg_duration, 2) if avg_duration else 0,
                "workflow_metrics": workflow_metrics,
                "languages": languages,
                "recommendations": recommendations,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to analyze repository: {str(e)}", exc_info=True)
            raise Exception(f"Failed to analyze repository: {str(e)}")
    
    async def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        event: Optional[str] = None,
        status: Optional[str] = None,
        per_page: int = 30,
        page: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get workflow runs for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Filter by branch
            event: Filter by event that triggered the workflow
            status: Filter by workflow run status
            per_page: Results per page (max 100)
            page: Page number
            
        Returns:
            Dictionary containing workflow runs and pagination info
        """
        try:
            repository = await self.get_repository(owner, repo)
            
            # Build query parameters
            query_params = {}
            if branch:
                query_params["branch"] = branch
            if event:
                query_params["event"] = event
            if status:
                query_params["status"] = status
            
            # Get workflow runs with pagination
            workflow_runs = repository.get_workflow_runs(**query_params)
            
            # Apply pagination
            total_count = workflow_runs.totalCount
            runs_page = list(workflow_runs.get_page(page - 1))  # GitHub is 0-based for pages
            
            # Format runs
            runs = []
            for run in runs_page:
                runs.append({
                    "id": run.id,
                    "name": run.name,
                    "head_branch": run.head_branch,
                    "head_sha": run.head_sha,
                    "run_number": run.run_number,
                    "event": run.event,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "workflow_id": run.workflow_id,
                    "url": run.html_url,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                    "updated_at": run.updated_at.isoformat() if run.updated_at else None,
                    "run_started_at": run.run_started_at.isoformat() if run.run_started_at else None,
                    "duration_seconds": (run.updated_at - run.created_at).total_seconds() 
                                      if run.updated_at and run.created_at else None
                })
            
            return {
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "workflow_runs": runs
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow runs: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get workflow runs: {str(e)}")
    
    async def get_workflow_run_logs(
        self,
        owner: str,
        repo: str,
        run_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get logs for a specific workflow run.
        
        Args:
            owner: Repository owner
            repo: Repository name
            run_id: ID of the workflow run
            
        Returns:
            Dictionary containing log information
        """
        try:
            repository = await self.get_repository(owner, repo)
            
            # Get the workflow run
            run = repository.get_workflow_run(run_id)
            
            # Get the logs URL (GitHub provides a zip file of logs)
            logs_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
            
            return {
                "run_id": run.id,
                "status": run.status,
                "conclusion": run.conclusion,
                "logs_url": logs_url,
                "artifacts_url": run.artifacts_url,
                "jobs_url": run.jobs_url
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow run logs: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get workflow run logs: {str(e)}")
    
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new GitHub issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body
            labels: Labels to apply to the issue
            assignees: Usernames to assign to the issue
            
        Returns:
            Dictionary containing the created issue details
        """
        try:
            repository = await self.get_repository(owner, repo)
            
            # Create the issue
            issue = repository.create_issue(
                title=title,
                body=body,
                labels=labels or [],
                assignees=assignees or []
            )
            
            return {
                "id": issue.id,
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "url": issue.html_url,
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees]
            }
            
        except Exception as e:
            logger.error(f"Failed to create issue: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create issue: {str(e)}")

# Create a singleton instance
github_tools = GitHubTools()

# Tool registration functions
def register_github_tools(mcp_server):
    """Register GitHub tools with the MCP server."""
    # Register analyze repository tool
    mcp_server.register_tool(
        ANALYZE_REPO_TOOL,
        github_tools.analyze_repository
    )
    
    # Register get workflow runs tool
    mcp_server.register_tool(
        GET_WORKFLOW_RUNS_TOOL,
        github_tools.get_workflow_runs
    )
    
    # Register get workflow run logs tool
    mcp_server.register_tool(
        GET_WORKFLOW_RUN_LOGS_TOOL,
        github_tools.get_workflow_run_logs
    )
    
    # Register create issue tool
    mcp_server.register_tool(
        CREATE_ISSUE_TOOL,
        github_tools.create_issue
    )
    
    logger.info("Registered GitHub tools with MCP server")
