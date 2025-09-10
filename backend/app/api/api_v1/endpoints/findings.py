from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from .... import crud, models, schemas
from ....database import get_db, get_db_session
from ....core.security import get_current_active_user
from ....schemas.repository import FindingStatus, FindingSeverity, FindingType

router = APIRouter()

@router.get("/", response_model=List[schemas.Finding])
async def list_findings(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    repository_id: Optional[int] = None,
    scan_id: Optional[int] = None,
    status: Optional[FindingStatus] = None,
    severity: Optional[FindingSeverity] = None,
    finding_type: Optional[FindingType] = None,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve findings with optional filtering.
    """
    # If repository_id is provided, check if the user has access to it
    if repository_id is not None:
        repository = crud.repository.get(db, id=repository_id)
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found",
            )
        
        if not crud.user.is_superuser(current_user) and (repository.owner_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    # If scan_id is provided, check if the user has access to it
    if scan_id is not None:
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
        
        # If both repository_id and scan_id are provided, ensure they match
        if repository_id is not None and scan.repository_id != repository_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scan does not belong to the specified repository",
            )
    
    # Get the findings with the specified filters
    findings = crud.finding.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        repository_id=repository_id,
        scan_id=scan_id,
        status=status,
        severity=severity,
        finding_type=finding_type,
        user_id=None if crud.user.is_superuser(current_user) else current_user.id
    )
    
    return findings

@router.get("/{finding_id}", response_model=schemas.Finding)
def read_finding(
    *,
    db: Session = Depends(get_db),
    finding_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific finding by ID.
    """
    finding = crud.finding.get(db, id=finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )
    
    # Check if the user has access to this finding's repository
    if not crud.user.is_superuser(current_user) and (finding.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return finding

@router.patch("/{finding_id}", response_model=schemas.Finding)
def update_finding(
    *,
    db: Session = Depends(get_db),
    finding_id: int,
    finding_in: schemas.FindingUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Update a finding.
    """
    # First get the finding
    finding = crud.finding.get(db, id=finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )
    
    # Check if the user has permission to update this finding
    if not crud.user.is_superuser(current_user) and (finding.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Update the finding
    finding = crud.finding.update(db, db_obj=finding, obj_in=finding_in)
    
    # If the status is being updated, create an audit log entry
    if finding_in.status is not None and finding_in.status != finding.status:
        # In a real implementation, you would create an audit log entry here
        pass
    
    return finding

@router.delete("/{finding_id}", response_model=schemas.Finding)
def delete_finding(
    *,
    db: Session = Depends(get_db),
    finding_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a finding.
    """
    # First get the finding
    finding = crud.finding.get(db, id=finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )
    
    # Check if the user has permission to delete this finding
    if not crud.user.is_superuser(current_user) and (finding.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Delete the finding
    finding = crud.finding.remove(db, id=finding_id)
    return finding

@router.get("/{finding_id}/recommendations", response_model=List[schemas.Recommendation])
def get_finding_recommendations(
    *,
    db: Session = Depends(get_db),
    finding_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get recommendations for a specific finding.
    """
    # First get the finding
    finding = crud.finding.get(db, id=finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )
    
    # Check if the user has access to this finding's repository
    if not crud.user.is_superuser(current_user) and (finding.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get the recommendations for this finding
    recommendations = crud.recommendation.get_multi_by_finding(
        db, finding_id=finding_id
    )
    
    return recommendations

@router.post("/{finding_id}/recommendations", response_model=schemas.Recommendation, status_code=status.HTTP_201_CREATED)
def create_finding_recommendation(
    *,
    db: Session = Depends(get_db),
    finding_id: int,
    recommendation_in: schemas.RecommendationCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new recommendation for a finding.
    """
    # First get the finding
    finding = crud.finding.get(db, id=finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )
    
    # Check if the user has permission to create a recommendation for this finding
    if not crud.user.is_superuser(current_user) and (finding.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Set the repository_id and finding_id from the finding
    recommendation_in.repository_id = finding.repository_id
    recommendation_in.finding_id = finding.id
    
    # Set the created_by user if not provided
    if not recommendation_in.created_by:
        recommendation_in.created_by = current_user.id
    
    # Create the recommendation
    recommendation = crud.recommendation.create(db, obj_in=recommendation_in)
    
    # Update the finding status if needed
    if finding.status != schemas.FindingStatus.IN_PROGRESS:
        crud.finding.update(
            db,
            db_obj=finding,
            obj_in={"status": schemas.FindingStatus.IN_PROGRESS}
        )
    
    return recommendation

@router.get("/{finding_id}/timeline", response_model=List[dict])
def get_finding_timeline(
    *,
    db: Session = Depends(get_db),
    finding_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get the timeline of events for a finding.
    """
    # First get the finding
    finding = crud.finding.get(db, id=finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )
    
    # Check if the user has access to this finding's repository
    if not crud.user.is_superuser(current_user) and (finding.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # In a real implementation, you would retrieve the timeline events from an audit log
    # For now, we'll return a simple timeline based on the finding's metadata
    timeline = []
    
    # Add creation event
    timeline.append({
        "event_type": "finding_created",
        "timestamp": finding.created_at.isoformat(),
        "user_id": finding.scan.triggered_by if finding.scan else None,
        "details": "Finding was created"
    })
    
    # Add status change events
    if finding.status_updated_at and finding.status_updated_at != finding.created_at:
        timeline.append({
            "event_type": "status_changed",
            "timestamp": finding.status_updated_at.isoformat(),
            "user_id": finding.updated_by,
            "details": f"Status changed to {finding.status}"
        })
    
    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x["timestamp"])
    
    return timeline
