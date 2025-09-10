from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from .... import crud, models, schemas
from ....db.session import get_db
from ....core.security import get_current_active_user
from ....services.github_service import GitHubService

router = APIRouter()

@router.get("/", response_model=List[schemas.Scan])
def list_scans(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve scans across all repositories (admin only).
    """
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    scans = crud.scan.get_multi(db, skip=skip, limit=limit)
    return scans

@router.get("/{scan_id}", response_model=schemas.ScanWithFindings)
def read_scan(
    *,
    db: Session = Depends(get_db),
    scan_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get scan by ID with findings.
    """
    scan = crud.scan.get_with_findings(db, id=scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )
    
    # Check if the user has access to this scan's repository
    if not crud.user.is_superuser(current_user) and (scan.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return scan

@router.patch("/{scan_id}", response_model=schemas.Scan)
def update_scan(
    *,
    db: Session = Depends(get_db),
    scan_id: int,
    scan_in: schemas.ScanUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Update a scan.
    """
    scan = crud.scan.get(db, id=scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )
    
    # Check if the user has permission to update this scan
    if not crud.user.is_superuser(current_user) and (scan.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    scan = crud.scan.update(db, db_obj=scan, obj_in=scan_in)
    return scan

@router.delete("/{scan_id}", response_model=schemas.Scan)
def delete_scan(
    *,
    db: Session = Depends(get_db),
    scan_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a scan.
    """
    scan = crud.scan.get(db, id=scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )
    
    # Check if the user has permission to delete this scan
    if not crud.user.is_superuser(current_user) and (scan.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    scan = crud.scan.remove(db, id=scan_id)
    return scan

@router.get("/{scan_id}/findings", response_model=List[schemas.Finding])
def list_scan_findings(
    *,
    db: Session = Depends(get_db),
    scan_id: int,
    status: Optional[schemas.FindingStatus] = None,
    severity: Optional[schemas.FindingSeverity] = None,
    finding_type: Optional[schemas.FindingType] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get findings for a specific scan.
    """
    # First check if the scan exists and the user has access
    scan = crud.scan.get(db, id=scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )
    
    if not crud.user.is_superuser(current_user) and (scan.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get findings with optional filters
    findings = crud.finding.get_multi_by_scan(
        db,
        scan_id=scan_id,
        status=status,
        severity=severity,
        finding_type=finding_type,
        skip=skip,
        limit=limit
    )
    return findings

@router.get("/{scan_id}/summary", response_model=schemas.ScanSummary)
def get_scan_summary(
    *,
    db: Session = Depends(get_db),
    scan_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get summary of findings for a scan.
    """
    # First check if the scan exists and the user has access
    scan = crud.scan.get(db, id=scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )
    
    if not crud.user.is_superuser(current_user) and (scan.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return crud.scan.get_summary(db, scan_id=scan_id)

@router.post("/{scan_id}/trigger-github-scan", response_model=schemas.Scan)
def trigger_github_scan(
    *,
    db: Session = Depends(get_db),
    scan_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Trigger a new GitHub scan for a repository.
    """
    # First check if the scan exists and the user has access
    scan = crud.scan.get(db, id=scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )
    
    if not crud.user.is_superuser(current_user) and (scan.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if the repository is a GitHub repository
    if scan.repository.provider != "github":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint only supports GitHub repositories",
        )
    
    # Get the GitHub integration for this repository
    github_integration = crud.github_integration.get_by_repository_id(
        db, repository_id=scan.repository_id
    )
    
    if not github_integration or not github_integration.access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub integration not configured for this repository",
        )
    
    try:
        # Initialize GitHub service
        github_service = GitHubService(access_token=github_integration.access_token)
        
        # Extract owner and repo from repository URL
        # Assuming the URL is in format: https://github.com/owner/repo
        parts = scan.repository.url.strip("/").split("/")
        if len(parts) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid repository URL format",
            )
        
        owner = parts[-2]
        repo_name = parts[-1]
        
        # Create a new scan record
        scan_in = schemas.ScanCreate(
            repository_id=scan.repository_id,
            status=schemas.ScanStatus.IN_PROGRESS,
            triggered_by=current_user.id,
        )
        new_scan = crud.scan.create(db, obj_in=scan_in)
        
        # In a real implementation, you would:
        # 1. Trigger an async task to perform the scan
        # 2. Update the scan status when complete
        # 3. Store the findings in the database
        
        # For now, we'll just return the new scan
        return new_scan
        
    except Exception as e:
        # Update scan status to failed
        if 'new_scan' in locals():
            crud.scan.update(
                db, 
                db_obj=new_scan, 
                obj_in={"status": schemas.ScanStatus.FAILED, "error_message": str(e)[:500]}
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger GitHub scan: {str(e)}",
        )

@router.post("/{scan_id}/generate-recommendations", response_model=List[schemas.Recommendation])
def generate_recommendations(
    *,
    db: Session = Depends(get_db),
    scan_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Generate recommendations based on scan findings.
    """
    # First check if the scan exists and the user has access
    scan = crud.scan.get(db, id=scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )
    
    if not crud.user.is_superuser(current_user) and (scan.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get all findings for this scan
    findings = crud.finding.get_multi_by_scan(db, scan_id=scan_id, limit=1000)
    
    if not findings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No findings found for this scan",
        )
    
    # In a real implementation, you would:
    # 1. Analyze findings to generate recommendations
    # 2. Create recommendation records in the database
    # 3. Return the generated recommendations
    
    # For now, we'll return an empty list
    return []
