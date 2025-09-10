from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from .... import crud, models, schemas
from ....db.session import get_db
from ....core.security import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[schemas.Repository])
def list_repositories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve repositories.
    """
    if crud.user.is_superuser(current_user):
        repositories = crud.repository.get_multi(db, skip=skip, limit=limit)
    else:
        repositories = crud.repository.get_multi_by_owner(
            db=db, owner_id=current_user.id, skip=skip, limit=limit
        )
    return repositories

@router.post("/", response_model=schemas.Repository, status_code=status.HTTP_201_CREATED)
def create_repository(
    *,
    db: Session = Depends(get_db),
    repository_in: schemas.RepositoryCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Create new repository.
    """
    # Check if the repository already exists
    repository = crud.repository.get_by_provider_id(db, provider_id=repository_in.provider_id)
    if repository:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A repository with this provider ID already exists.",
        )
    
    # Only allow users to create repositories for themselves unless they're superusers
    if not crud.user.is_superuser(current_user) and repository_in.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    repository = crud.repository.create_with_owner(
        db=db, obj_in=repository_in, owner_id=current_user.id
    )
    return repository

@router.get("/{repository_id}", response_model=schemas.Repository)
def read_repository(
    *,
    db: Session = Depends(get_db),
    repository_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get repository by ID.
    """
    repository = crud.repository.get(db, id=repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
    
    # Check if the user has access to this repository
    if not crud.user.is_superuser(current_user) and (repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return repository

@router.put("/{repository_id}", response_model=schemas.Repository)
def update_repository(
    *,
    db: Session = Depends(get_db),
    repository_id: int,
    repository_in: schemas.RepositoryUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Update a repository.
    """
    repository = crud.repository.get(db, id=repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
    
    # Check if the user has permission to update this repository
    if not crud.user.is_superuser(current_user) and (repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    repository = crud.repository.update(db, db_obj=repository, obj_in=repository_in)
    return repository

@router.delete("/{repository_id}", response_model=schemas.Repository)
def delete_repository(
    *,
    db: Session = Depends(get_db),
    repository_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a repository.
    """
    repository = crud.repository.get(db, id=repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
    
    # Check if the user has permission to delete this repository
    if not crud.user.is_superuser(current_user) and (repository.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    repository = crud.repository.remove(db, id=repository_id)
    return repository

@router.get("/{repository_id}/scans", response_model=List[schemas.Scan])
def list_repository_scans(
    *,
    db: Session = Depends(get_db),
    repository_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get scans for a specific repository.
    """
    # First check if the repository exists and the user has access
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
    
    scans = crud.scan.get_multi_by_repository(
        db, repository_id=repository_id, skip=skip, limit=limit
    )
    return scans

@router.post("/{repository_id}/scans", response_model=schemas.Scan, status_code=status.HTTP_201_CREATED)
def create_repository_scan(
    *,
    db: Session = Depends(get_db),
    repository_id: int,
    scan_in: schemas.ScanCreate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new scan for a repository.
    """
    # First check if the repository exists and the user has access
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
    
    # Set the repository_id from the URL path
    scan_in.repository_id = repository_id
    
    # Set the user who triggered the scan
    if not scan_in.triggered_by:
        scan_in.triggered_by = current_user.id
    
    scan = crud.scan.create(db, obj_in=scan_in)
    return scan

@router.get("/{repository_id}/summary", response_model=schemas.RepositoryScanSummary)
def get_repository_summary(
    *,
    db: Session = Depends(get_db),
    repository_id: int,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get summary of scans and findings for a repository.
    """
    # First check if the repository exists and the user has access
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
    
    # Get the last scan
    last_scan = crud.scan.get_latest_by_repository(db, repository_id=repository_id)
    
    # Get scan summary
    scan_summary = crud.scan.get_summary(db, repository_id=repository_id)
    
    # Get repository stats
    total_scans = crud.scan.count_by_repository(db, repository_id=repository_id)
    total_findings = crud.finding.count_by_repository(db, repository_id=repository_id)
    open_findings = crud.finding.count_by_repository_and_status(
        db, repository_id=repository_id, status=schemas.FindingStatus.OPEN
    )
    
    return {
        "repository": repository,
        "last_scan": last_scan,
        "total_scans": total_scans,
        "total_findings": total_findings,
        "open_findings": open_findings,
        "scan_summary": scan_summary,
    }
