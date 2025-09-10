import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import math

from ..config import settings

logger = logging.getLogger(__name__)

class CarbonCalculator:
    """Service for calculating carbon emissions from CI/CD workflows."""
    
    # Average power consumption in watts for different machine types
    # Sources: Various cloud provider specifications and research papers
    MACHINE_POWER_CONSUMPTION = {
        "ubuntu-latest": 8.0,      # 2-core VM
        "ubuntu-20.04": 8.0,       # 2-core VM
        "ubuntu-22.04": 8.0,       # 2-core VM
        "windows-latest": 15.0,    # Windows runner (higher due to OS overhead)
        "windows-2022": 15.0,
        "windows-2019": 16.0,
        "macos-latest": 12.0,      # macOS runner
        "macos-12": 12.0,
        "macos-13": 11.5,          # Newer macOS versions might be more efficient
        "self-hosted": 100.0,      # Default for self-hosted runners
        "large": 32.0,             # 8-core VM
        "xlarge": 64.0,            # 16-core VM
        "2xlarge": 128.0,          # 32-core VM
    }
    
    # Default carbon intensity in kg CO2e per kWh
    # Source: https://www.iea.org/reports/global-energy-co2-status-report-2019/emissions
    DEFAULT_CARBON_INTENSITY = 0.5  # Global average
    
    def __init__(
        self, 
        carbon_intensity: Optional[float] = None,
        cost_per_kwh: Optional[float] = None
    ):
        """Initialize the carbon calculator.
        
        Args:
            carbon_intensity: Carbon intensity in kg CO2e per kWh. If not provided,
                            uses the value from settings or default.
            cost_per_kwh: Cost of electricity in USD per kWh. Used for cost estimation.
        """
        self.carbon_intensity = carbon_intensity or float(settings.CARBON_INTENSITY)
        self.cost_per_kwh = cost_per_kwh or float(settings.COST_PER_KWH)
    
    def calculate_emissions(
        self,
        duration_seconds: float,
        machine_type: str = "ubuntu-latest",
        cpu_usage: float = 1.0,
        memory_gb: Optional[float] = None,
        region: Optional[str] = None,
    ) -> Dict[str, float]:
        """Calculate carbon emissions for a CI/CD job.
        
        Args:
            duration_seconds: Duration of the job in seconds.
            machine_type: Type of machine/runner used (e.g., 'ubuntu-latest').
            cpu_usage: CPU utilization factor (0.0 to 1.0).
            memory_gb: Amount of memory used in GB (optional).
            region: Cloud region (optional, for region-specific calculations).
            
        Returns:
            Dictionary containing:
            - emissions_kg: Carbon emissions in kg CO2e
            - energy_kwh: Energy consumption in kWh
            - estimated_cost: Estimated cost in USD
        """
        # Get power consumption for the machine type
        power_watts = self.MACHINE_POWER_CONSUMPTION.get(
            machine_type.lower(),
            self.MACHINE_POWER_CONSUMPTION["ubuntu-latest"]
        )
        
        # Adjust for CPU utilization
        adjusted_power = power_watts * cpu_usage
        
        # Convert duration to hours
        duration_hours = duration_seconds / 3600
        
        # Calculate energy consumption in kWh
        energy_kwh = (adjusted_power * duration_hours) / 1000
        
        # Calculate carbon emissions
        emissions_kg = energy_kwh * self.carbon_intensity
        
        # Calculate estimated cost
        estimated_cost = energy_kwh * self.cost_per_kwh
        
        return {
            "emissions_kg": round(emissions_kg, 6),  # 1g precision
            "energy_kwh": round(energy_kwh, 6),
            "estimated_cost": round(estimated_cost, 4),
            "machine_type": machine_type,
            "duration_seconds": duration_seconds,
            "carbon_intensity": self.carbon_intensity,
            "cost_per_kwh": self.cost_per_kwh
        }
    
    def analyze_workflow_run(
        self, 
        workflow_data: Dict[str, Any],
        job_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze a GitHub Actions workflow run for carbon emissions.
        
        Args:
            workflow_data: Dictionary containing workflow metadata.
            job_data: List of job data dictionaries.
            
        Returns:
            Dictionary with analysis results.
        """
        total_emissions = 0.0
        total_energy = 0.0
        total_cost = 0.0
        
        job_analyses = []
        
        for job in job_data:
            # Get job duration in seconds
            started_at = datetime.fromisoformat(job["started_at"].replace("Z", "+00:00"))
            completed_at = datetime.fromisoformat(job["completed_at"].replace("Z", "+00:00"))
            duration_seconds = (completed_at - started_at).total_seconds()
            
            # Get machine type from runner name or labels
            runner_name = job.get("runner_name", "")
            runner_labels = job.get("labels", [])
            
            # Try to determine machine type from labels
            machine_type = "ubuntu-latest"  # Default
            for label in runner_labels:
                if any(os in label.lower() for os in ["ubuntu", "windows", "macos"]):
                    machine_type = label
                    break
            
            # Calculate emissions for this job
            job_result = self.calculate_emissions(
                duration_seconds=duration_seconds,
                machine_type=machine_type,
                cpu_usage=0.8  # Default assumption of 80% CPU usage
            )
            
            total_emissions += job_result["emissions_kg"]
            total_energy += job_result["energy_kwh"]
            total_cost += job_result["estimated_cost"]
            
            job_analyses.append({
                "job_id": job["id"],
                "job_name": job["name"],
                "duration_seconds": duration_seconds,
                "machine_type": machine_type,
                **job_result
            })
        
        # Calculate potential savings
        potential_savings = self.calculate_potential_savings(job_analyses)
        
        return {
            "workflow_id": workflow_data["id"],
            "workflow_name": workflow_data["name"],
            "run_id": workflow_data["run_id"],
            "run_number": workflow_data["run_number"],
            "event": workflow_data["event"],
            "status": workflow_data["status"],
            "conclusion": workflow_data.get("conclusion"),
            "created_at": workflow_data["created_at"],
            "updated_at": workflow_data["updated_at"],
            "total_emissions_kg": round(total_emissions, 6),
            "total_energy_kwh": round(total_energy, 6),
            "total_cost_usd": round(total_cost, 4),
            "jobs": job_analyses,
            "potential_savings": potential_savings,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def calculate_potential_savings(
        self, 
        job_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate potential savings from optimization opportunities.
        
        Args:
            job_analyses: List of job analysis results.
            
        Returns:
            Dictionary with potential savings information.
        """
        total_current_emissions = sum(job["emissions_kg"] for job in job_analyses)
        total_current_cost = sum(job["estimated_cost"] for job in job_analyses)
        
        opportunities = []
        
        # 1. Caching opportunity analysis
        cache_opportunity = self._analyze_caching_opportunity(job_analyses)
        if cache_opportunity:
            opportunities.append(cache_opportunity)
        
        # 2. Machine type optimization
        machine_opportunity = self._analyze_machine_optimization(job_analyses)
        if machine_opportunity:
            opportunities.append(machine_opportunity)
        
        # 3. Job scheduling optimization
        schedule_opportunity = self._analyze_scheduling_opportunity(job_analyses)
        if schedule_opportunity:
            opportunities.append(schedule_opportunity)
        
        # Calculate total potential savings
        total_savings_emissions = sum(opp["emissions_savings_kg"] for opp in opportunities)
        total_savings_cost = sum(opp["cost_savings_usd"] for opp in opportunities)
        
        return {
            "total_emissions_savings_kg": round(total_savings_emissions, 6),
            "total_cost_savings_usd": round(total_savings_cost, 4),
            "percent_emissions_savings": round((total_savings_emissions / total_current_emissions) * 100, 2) if total_current_emissions > 0 else 0,
            "percent_cost_savings": round((total_savings_cost / total_current_cost) * 100, 2) if total_current_cost > 0 else 0,
            "opportunities": opportunities
        }
    
    def _analyze_caching_opportunity(
        self, 
        job_analyses: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze potential caching opportunities."""
        # This is a simplified analysis - in a real implementation, you'd analyze
        # the actual workflow files to detect caching opportunities
        
        # Look for jobs that take a long time but could benefit from caching
        cache_candidates = []
        
        for job in job_analyses:
            if job["duration_seconds"] > 120:  # Jobs longer than 2 minutes
                cache_candidates.append(job)
        
        if not cache_candidates:
            return None
        
        # Estimate potential savings (simplified)
        avg_savings_pct = 0.3  # 30% time reduction with caching
        
        total_savings_emissions = 0.0
        total_savings_cost = 0.0
        
        for job in cache_candidates:
            savings_emissions = job["emissions_kg"] * avg_savings_pct
            savings_cost = job["estimated_cost"] * avg_savings_pct
            
            total_savings_emissions += savings_emissions
            total_savings_cost += savings_cost
        
        return {
            "type": "caching",
            "description": "Add caching for dependencies and build outputs",
            "emissions_savings_kg": round(total_savings_emissions, 6),
            "cost_savings_usd": round(total_savings_cost, 4),
            "jobs_affected": len(cache_candidates),
            "estimated_effort": "1-2 hours",
            "difficulty": "low"
        }
    
    def _analyze_machine_optimization(
        self, 
        job_analyses: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze potential machine type optimizations."""
        # Look for jobs that might be using more resources than needed
        optimization_candidates = []
        
        for job in job_analyses:
            machine_type = job["machine_type"].lower()
            
            # Check if this is a large machine that might be underutilized
            if "large" in machine_type and job["duration_seconds"] < 300:  # Less than 5 minutes
                optimization_candidates.append(job)
            # Check for Windows runners when Linux could be used
            elif "windows" in machine_type and not any(
                ext in job.get("job_name", "").lower() 
                for ext in ["windows", "win", ".net", "c#", "csharp"]
            ):
                optimization_candidates.append(job)
        
        if not optimization_candidates:
            return None
        
        # Estimate potential savings (simplified)
        avg_savings_pct = 0.4  # 40% cost reduction by using more appropriate machine
        
        total_savings_emissions = 0.0
        total_savings_cost = 0.0
        
        for job in optimization_candidates:
            savings_emissions = job["emissions_kg"] * avg_savings_pct
            savings_cost = job["estimated_cost"] * avg_savings_pct
            
            total_savings_emissions += savings_emissions
            total_savings_cost += savings_cost
        
        return {
            "type": "machine_optimization",
            "description": "Optimize machine types based on workload requirements",
            "emissions_savings_kg": round(total_savings_emissions, 6),
            "cost_savings_usd": round(total_savings_cost, 4),
            "jobs_affected": len(optimization_candidates),
            "estimated_effort": "2-4 hours",
            "difficulty": "medium"
        }
    
    def _analyze_scheduling_opportunity(
        self, 
        job_analyses: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze potential scheduling optimizations."""
        # This would analyze the workflow schedule and job dependencies
        # to find opportunities for parallelization or batching
        
        # For now, we'll just check if there are sequential jobs that could run in parallel
        if len(job_analyses) < 2:
            return None
        
        # Simple check: if jobs are running sequentially but don't depend on each other
        sequential_jobs = []
        
        for i in range(len(job_analyses) - 1):
            current_job = job_analyses[i]
            next_job = job_analyses[i + 1]
            
            # If jobs overlap in time, they're already running in parallel
            current_end = current_job.get("started_at", "") + timedelta(seconds=current_job["duration_seconds"])
            next_start = next_job.get("started_at", "")
            
            if isinstance(current_end, str):
                current_end = datetime.fromisoformat(current_end.replace("Z", "+00:00"))
            if isinstance(next_start, str):
                next_start = datetime.fromisoformat(next_start.replace("Z", "+00:00"))
            
            if next_start >= current_end:
                # Jobs are sequential, check if they could run in parallel
                if not self._jobs_have_dependency(current_job, next_job):
                    sequential_jobs.append((current_job, next_job))
        
        if not sequential_jobs:
            return None
        
        # Estimate potential savings (simplified)
        # Assuming we can run 2 jobs in parallel, reducing total time by ~50%
        total_savings_emissions = 0.0
        total_savings_cost = 0.0
        
        for job1, job2 in sequential_jobs:
            # The savings would be the duration of the shorter job
            # since that's how much time we'd save by running in parallel
            shorter_duration = min(job1["duration_seconds"], job2["duration_seconds"])
            
            # Calculate emissions and cost for the saved time
            # We'll use the average of the two jobs' metrics
            avg_emissions_rate = (job1["emissions_kg"] / job1["duration_seconds"] + 
                                 job2["emissions_kg"] / job2["duration_seconds"]) / 2
            avg_cost_rate = (job1["estimated_cost"] / job1["duration_seconds"] + 
                            job2["estimated_cost"] / job2["duration_seconds"]) / 2
            
            total_savings_emissions += avg_emissions_rate * shorter_duration
            total_savings_cost += avg_cost_rate * shorter_duration
        
        return {
            "type": "parallelization",
            "description": "Run independent jobs in parallel to reduce total execution time",
            "emissions_savings_kg": round(total_savings_emissions, 6),
            "cost_savings_usd": round(total_savings_cost, 4),
            "jobs_affected": len(sequential_jobs) * 2,
            "estimated_effort": "2-5 hours",
            "difficulty": "medium"
        }
    
    def _jobs_have_dependency(
        self, 
        job1: Dict[str, Any], 
        job2: Dict[str, Any]
    ) -> bool:
        """Check if there's a dependency between two jobs."""
        # This is a simplified check - in a real implementation, you'd parse
        # the workflow file to determine actual dependencies
        
        # Check if job2 depends on job1's outputs
        job1_outputs = [f"${{{{ steps.{step}.outputs }}}}" for step in job1.get("steps", [])]
        
        for step in job2.get("steps", []):
            for output in job1_outputs:
                if output in step.get("with", {}) or output in step.get("env", {}):
                    return True
        
        return False
