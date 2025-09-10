import logging
from typing import Dict, List, Optional, Any
from github import Github, GithubIntegration, Auth
from github.Repository import Repository as GithubRepository
from github.Workflow import Workflow
from github.WorkflowRun import WorkflowRun
from github.PullRequest import PullRequest as GithubPullRequest

from ..config import settings
from ..models.repository import Repository, RepositoryScan, ScanFinding, ScanFindingType, ScanFindingSeverity
from ..database import get_db_session

logger = logging.getLogger(__name__)

class GitHubService:
    """Service for interacting with the GitHub API."""
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize the GitHub service.
        
        Args:
            access_token: GitHub personal access token or installation access token.
                         If not provided, will use the GitHub App credentials.
        """
        self.access_token = access_token
        self.github = self._get_github_client()
    
    def _get_github_client(self):
        """Get a GitHub client instance."""
        if self.access_token:
            return Github(self.access_token)
        
        # Use GitHub App credentials if no access token is provided
        if not settings.GITHUB_APP_ID or not settings.GITHUB_APP_PRIVATE_KEY:
            raise ValueError(
                "GitHub App credentials (GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY) "
                "are required when no access token is provided"
            )
            
        # Create a GitHub integration instance
        auth = Auth.AppAuth(
            settings.GITHUB_APP_ID,
            settings.GITHUB_APP_PRIVATE_KEY
        )
        return GithubIntegration(auth=auth)
    
    def get_repository(self, owner: str, repo_name: str) -> GithubRepository:
        """Get a GitHub repository."""
        return self.github.get_repo(f"{owner}/{repo_name}")
    
    def get_workflows(self, owner: str, repo_name: str) -> List[Workflow]:
        """Get all workflows for a repository."""
        repo = self.get_repository(owner, repo_name)
        return list(repo.get_workflows())
    
    def get_workflow_runs(self, owner: str, repo_name: str, workflow_id: Optional[int] = None) -> List[WorkflowRun]:
        """Get workflow runs for a repository or a specific workflow."""
        repo = self.get_repository(owner, repo_name)
        if workflow_id:
            workflow = repo.get_workflow(workflow_id)
            return list(workflow.get_runs())
        return list(repo.get_workflow_runs())
    
    def analyze_workflow(self, owner: str, repo_name: str, workflow_path: str) -> Dict[str, Any]:
        """Analyze a GitHub Actions workflow for potential optimizations."""
        repo = self.get_repository(owner, repo_name)
        workflow = repo.get_workflow(workflow_path)
        runs = workflow.get_runs()
        
        # Get the most recent runs for analysis
        recent_runs = list(runs[:10])  # Analyze last 10 runs
        
        # Calculate metrics
        total_duration = sum(run.timing() for run in recent_runs if run.timing() is not None)
        avg_duration = total_duration / len(recent_runs) if recent_runs else 0
        
        # Check for common issues
        issues = []
        
        # 1. Check for long-running jobs
        if avg_duration > 10 * 60:  # More than 10 minutes
            issues.append({
                "type": "LONG_RUNNING_JOBS",
                "severity": "medium",
                "message": f"Average workflow duration is {avg_duration/60:.1f} minutes. Consider optimizing long-running jobs.",
                "suggestion": "Split long-running jobs into smaller, parallel jobs where possible."
            })
        
        # 2. Check for cache usage
        workflow_content = repo.get_contents(workflow_path).decoded_content.decode()
        if "actions/cache@" not in workflow_content:
            issues.append({
                "type": "MISSING_CACHE",
                "severity": "high",
                "message": "No caching detected in workflow.",
                "suggestion": "Use actions/cache to cache dependencies and build outputs to speed up workflows."
            })
        
        # 3. Check for scheduled runs frequency
        if "schedule:" in workflow_content:
            # Parse schedule to check for frequent runs
            # This is a simplified check - a real implementation would parse the cron expression
            if "* * * * *" in workflow_content:  # Every minute
                issues.append({
                    "type": "FREQUENT_SCHEDULE",
                    "severity": "high",
                    "message": "Workflow is scheduled to run very frequently (every minute).",
                    "suggestion": "Consider if such frequent runs are necessary. Reduce frequency if possible."
                })
        
        return {
            "workflow_name": workflow.name,
            "path": workflow_path,
            "total_runs_analyzed": len(recent_runs),
            "average_duration_seconds": avg_duration,
            "success_rate": sum(1 for r in recent_runs if r.conclusion == "success") / len(recent_runs) if recent_runs else 0,
            "issues": issues
        }
    
    def create_scan_findings(self, db: Any, scan_id: int, owner: str, repo_name: str) -> List[ScanFinding]:
        """Create scan findings for a repository."""
        db = next(get_db_session()) if db is None else db
        
        try:
            # Get all workflows
            workflows = self.get_workflows(owner, repo_name)
            findings = []
            
            for workflow in workflows:
                # Analyze each workflow
                analysis = self.analyze_workflow(owner, repo_name, workflow.path)
                
                # Create findings for each issue
                for issue in analysis.get("issues", []):
                    finding = ScanFinding(
                        scan_id=scan_id,
                        finding_type=ScanFindingType.CI_OPTIMIZATION,
                        severity=ScanFindingSeverity(issue["severity"].lower()),
                        title=f"{issue['type']}: {issue['message']}",
                        description=issue.get("suggestion", ""),
                        file_path=workflow.path,
                        status="open",
                        estimated_cost_savings=self._estimate_cost_savings(issue, analysis),
                        estimated_carbon_reduction=self._estimate_carbon_reduction(issue, analysis),
                        recommended_fix=issue.get("suggestion", ""),
                        fix_difficulty="medium",
                        fix_effort="1-2 hours"
                    )
                    findings.append(finding)
            
            # Add findings to database
            db.add_all(findings)
            db.commit()
            
            return findings
            
        except Exception as e:
            logger.error(f"Error creating scan findings: {str(e)}")
            db.rollback()
            raise
    
    def _estimate_cost_savings(self, issue: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """Estimate cost savings for a finding."""
        # This is a simplified estimation - in a real implementation, you'd want to
        # consider more factors like GitHub Actions pricing, team size, etc.
        savings = 0.0
        
        if issue["type"] == "LONG_RUNNING_JOBS" and analysis["average_duration_seconds"] > 10 * 60:
            # Estimate $0.008 per minute for GitHub Actions
            # If we can reduce the duration by 30%, that's the potential savings per run
            reduction = analysis["average_duration_seconds"] * 0.3 / 60  # in minutes
            savings = reduction * 0.008 * 30  # Assuming 30 runs per month
        
        return round(savings, 2)
    
    def _estimate_carbon_reduction(self, issue: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """Estimate carbon reduction for a finding."""
        # This is a simplified estimation - in a real implementation, you'd want to
        # consider more factors like energy source, data center location, etc.
        reduction = 0.0
        
        if issue["type"] == "LONG_RUNNING_JOBS" and analysis["average_duration_seconds"] > 10 * 60:
            # Estimate 0.0005 kg CO2e per minute of compute time
            # If we can reduce the duration by 30%, that's the potential reduction per run
            reduction_seconds = analysis["average_duration_seconds"] * 0.3
            reduction = reduction_seconds / 60 * 0.0005 * 30  # kg CO2e per month (30 runs)
        
        return round(reduction, 4)
