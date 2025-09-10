from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from .... import crud, models, schemas
from ....db.session import get_db
from ....core.security import get_current_active_user
from ....services.github_service import GitHubService

router = APIRouter()

@router.get("/", response_model=List[schemas.RecommendationWithRelated])
def list_recommendations(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    repository_id: Optional[int] = None,
    scan_id: Optional[int] = None,
    finding_id: Optional[int] = None,
    status: Optional[schemas.RecommendationStatus] = None,
    impact: Optional[schemas.RecommendationImpact] = None,
    effort: Optional[schemas.RecommendationEffort] = None,
    recommendation_type: Optional[schemas.RecommendationType] = None,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve recommendations with optional filtering.
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
    
    # If finding_id is provided, check if the user has access to it
    if finding_id is not None:
        finding = crud.finding.get(db, id=finding_id)
        if not finding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Finding not found",
            )
        
        if not crud.user.is_superuser(current_user) and (finding.repository.owner_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    # Get the recommendations with the specified filters
    recommendations = crud.recommendation.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        repository_id=repository_id,
        scan_id=scan_id,
        finding_id=finding_id,
        status=status,
        impact=impact,
        effort=effort,
        recommendation_type=recommendation_type,
        user_id=None if crud.user.is_superuser(current_user) else current_user.id
    )
    
    return recommendations

@router.get("/{recommendation_id}", response_model=schemas.RecommendationWithRelated)
def read_recommendation(
    *,
    db: Session = Depends(get_db),
    recommendation_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific recommendation by ID with related entities.
    """
    recommendation = crud.recommendation.get_with_related(db, id=recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    
    # Check if the user has access to this recommendation's repository
    if not crud.user.is_superuser(current_user) and (recommendation.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return recommendation

@router.patch("/{recommendation_id}", response_model=schemas.Recommendation)
def update_recommendation(
    *,
    db: Session = Depends(get_db),
    recommendation_id: int,
    recommendation_in: schemas.RecommendationUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Update a recommendation.
    """
    # First get the recommendation
    recommendation = crud.recommendation.get(db, id=recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    
    # Check if the user has permission to update this recommendation
    if not crud.user.is_superuser(current_user) and (recommendation.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Update the recommendation
    recommendation = crud.recommendation.update(db, db_obj=recommendation, obj_in=recommendation_in)
    
    # If the status is being updated to IMPLEMENTED, update the related finding status
    if recommendation_in.status == schemas.RecommendationStatus.IMPLEMENTED and recommendation.finding_id:
        finding = crud.finding.get(db, id=recommendation.finding_id)
        if finding and finding.status != schemas.FindingStatus.RESOLVED:
            crud.finding.update(
                db,
                db_obj=finding,
                obj_in={"status": schemas.FindingStatus.RESOLVED}
            )
    
    return recommendation

@router.delete("/{recommendation_id}", response_model=schemas.Recommendation)
def delete_recommendation(
    *,
    db: Session = Depends(get_db),
    recommendation_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a recommendation.
    """
    # First get the recommendation
    recommendation = crud.recommendation.get(db, id=recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    
    # Check if the user has permission to delete this recommendation
    if not crud.user.is_superuser(current_user) and (recommendation.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Delete the recommendation
    recommendation = crud.recommendation.remove(db, id=recommendation_id)
    return recommendation

@router.post("/{recommendation_id}/implement", response_model=schemas.Recommendation)
def implement_recommendation(
    *,
    db: Session = Depends(get_db),
    recommendation_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Mark a recommendation as implemented.
    """
    # First get the recommendation
    recommendation = crud.recommendation.get(db, id=recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    
    # Check if the user has permission to update this recommendation
    if not crud.user.is_superuser(current_user) and (recommendation.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Update the recommendation status to IMPLEMENTED
    recommendation = crud.recommendation.update(
        db,
        db_obj=recommendation,
        obj_in={"status": schemas.RecommendationStatus.IMPLEMENTED}
    )
    
    # Update the related finding status to RESOLVED if this recommendation fixes it
    if recommendation.finding_id:
        finding = crud.finding.get(db, id=recommendation.finding_id)
        if finding and finding.status != schemas.FindingStatus.RESOLVED:
            crud.finding.update(
                db,
                db_obj=finding,
                obj_in={"status": schemas.FindingStatus.RESOLVED}
            )
    
    return recommendation

@router.post("/{recommendation_id}/create-pr", response_model=dict)
def create_pull_request_for_recommendation(
    *,
    db: Session = Depends(get_db),
    recommendation_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Create a pull request to implement a recommendation.
    """
    # First get the recommendation with related data
    recommendation = crud.recommendation.get_with_related(db, id=recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    
    # Check if the user has permission to create a PR for this recommendation
    if not crud.user.is_superuser(current_user) and (recommendation.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Check if the repository is a GitHub repository
    if recommendation.repository.provider != "github":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint only supports GitHub repositories",
        )
    
    # Get the GitHub integration for this repository
    github_integration = crud.github_integration.get_by_repository_id(
        db, repository_id=recommendation.repository_id
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
        parts = recommendation.repository.url.strip("/").split("/")
        if len(parts) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid repository URL format",
            )
        
        owner = parts[-2]
        repo_name = parts[-1]
        
        # Create a new branch for the fix
        branch_name = f"ecoci/fix-{recommendation_id}"
        
        # In a real implementation, you would:
        # 1. Create a new branch
        # 2. Make the necessary changes to implement the recommendation
        # 3. Commit the changes
        # 4. Create a pull request
        
        # For now, we'll just return a mock response
        pr_url = f"https://github.com/{owner}/{repo_name}/pull/1"
        
        # Update the recommendation with the PR URL
        recommendation = crud.recommendation.update(
            db,
            db_obj=recommendation,
            obj_in={
                "status": schemas.RecommendationStatus.APPROVED,
                "pr_url": pr_url
            }
        )
        
        return {
            "success": True,
            "pr_url": pr_url,
            "message": "Pull request created successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pull request: {str(e)}",
        )

@router.get("/{recommendation_id}/timeline", response_model=List[dict])
def get_recommendation_timeline(
    *,
    db: Session = Depends(get_db),
    recommendation_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get the timeline of events for a recommendation.
    """
    # First get the recommendation
    recommendation = crud.recommendation.get(db, id=recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    
    # Check if the user has access to this recommendation's repository
    if not crud.user.is_superuser(current_user) and (recommendation.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # In a real implementation, you would retrieve the timeline events from an audit log
    # For now, we'll return a simple timeline based on the recommendation's metadata
    timeline = []
    
    # Add creation event
    timeline.append({
        "event_type": "recommendation_created",
        "timestamp": recommendation.created_at.isoformat(),
        "user_id": recommendation.created_by,
        "details": "Recommendation was created"
    })
    
    # Add status change events
    if recommendation.updated_at and recommendation.updated_at != recommendation.created_at:
        timeline.append({
            "event_type": "status_changed",
            "timestamp": recommendation.updated_at.isoformat(),
            "user_id": recommendation.assigned_to,
            "details": f"Status changed to {recommendation.status}"
        })
    
    # Add PR creation event if applicable
    if recommendation.pr_url:
        timeline.append({
            "event_type": "pr_created",
            "timestamp": recommendation.updated_at.isoformat(),
            "user_id": recommendation.assigned_to,
            "details": f"Pull request created: {recommendation.pr_url}"
        })
    
    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x["timestamp"])
    
    return timeline

@router.get("/{recommendation_id}/comments", response_model=List[schemas.RecommendationComment])
def get_recommendation_comments(
    *,
    db: Session = Depends(get_db),
    recommendation_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get comments for a recommendation.
    """
    # First get the recommendation
    recommendation = crud.recommendation.get(db, id=recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    
    # Check if the user has access to this recommendation's repository
    if not crud.user.is_superuser(current_user) and (recommendation.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Get the comments for this recommendation
    comments = crud.recommendation_comment.get_multi_by_recommendation(
        db, recommendation_id=recommendation_id
    )
    
    return comments

@router.post("/{recommendation_id}/comments", response_model=schemas.RecommendationComment, status_code=status.HTTP_201_CREATED)
def create_recommendation_comment(
    *,
    db: Session = Depends(get_db),
    recommendation_id: int,
    comment_in: schemas.RecommendationCommentCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new comment on a recommendation.
    """
    # First get the recommendation
    recommendation = crud.recommendation.get(db, id=recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found",
        )
    
    # Check if the user has access to this recommendation's repository
    if not crud.user.is_superuser(current_user) and (recommendation.repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    # Set the user_id from the current user
    comment_in.user_id = current_user.id
    comment_in.recommendation_id = recommendation_id
    
    # Create the comment
    comment = crud.recommendation_comment.create(db, obj_in=comment_in)
    
    # Update the recommendation's updated_at timestamp
    crud.recommendation.update_timestamp(db, db_obj=recommendation)
    
    return comment
