from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.CRUD.service import Service_Crud
from app.database import get_db
from app.models import Service, User
from app.schemas.service import ServiceOut, ServiceCreate, ServiceUpdate
from app.schemas.user import Role
from app.security import get_current_user

service_router = APIRouter(prefix="/services", tags=["services"])


@service_router.get("/", response_model=List[ServiceOut])
def get_services(
        db: Session = Depends(get_db),
        q: Optional[str] = Query(None, description="Search query for title or description"),
        price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
        price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
        active: Optional[bool] = Query(True, description="Filter by active status")
):

    return Service_Crud.get_services(db,q, price_min, price_max, active)


@service_router.get("/{id}", response_model=ServiceOut)
def get_service(service_id: UUID,db: Session = Depends(get_db)):
    return Service_Crud.get_service(db, service_id)

@service_router.post("/", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
        service_data: ServiceCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):

    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create services"
        )

    existing_service = db.query(Service).filter(Service.title == service_data.title).first()
    if existing_service:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service with this title already exists"
        )

    service = Service(**service_data.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)

    return service


@service_router.patch("/{id}", response_model=ServiceOut)
def update_service(service_id: UUID, service_data: ServiceUpdate,
                   db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):

    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update services"
        )

    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    # Update only provided fields
    update_data = service_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)

    return service


# DELETE /services/{id} - Admin only
@service_router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
        service_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Delete a service (admin only).
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete services"
        )

    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    db.delete(service)
    db.commit()

    return None