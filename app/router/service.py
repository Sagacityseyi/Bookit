from csv import excel

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app import logger
from app.CRUD.service import Service_Crud
from app.database import get_db
from app.logger import get_logger
from app.models import Service, User
from app.schemas.service import ServiceOut, ServiceCreate, ServiceUpdate
from app.schemas.user import Role
from app.security import get_current_user

service_router = APIRouter(prefix="/services", tags=["services"])

logger = get_logger(__name__)

@service_router.get("/", response_model=ServiceOut)  # Or create a proper response model
def get_services(
    db: Session = Depends(get_db),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    active: Optional[bool] = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return")
):
    services, total = Service_Crud.get_services(
        db, price_min, price_max, active, skip, limit
    )

    return {
        "data": services,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@service_router.get("/{id}", response_model=ServiceOut)
def get_service(service_id: UUID,db: Session = Depends(get_db)):
    return Service_Crud.get_service(db, service_id)

@service_router.post("/", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
        service_data: ServiceCreate,
        db: Session = Depends(get_db),
        #current_user: User = Depends(get_current_user)
):
    #if current_user.role != Role.ADMIN:
       # raise HTTPException(
            #status_code=status.HTTP_403_FORBIDDEN,
         #   detail="Only administrators can create services"
       # )

    try:
        new_service = Service_Crud.create_service(db, service_data)
        logger.info("Service created successfully")

        db.commit()
        return new_service

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unable to create service..")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during service creation: {str(e)}"
        )


@service_router.patch("/{id}", response_model=ServiceOut)
def update_service(
        service_id: UUID,
        service_data: ServiceUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update services"
        )

    try:
        service = Service_Crud.update_service(db, service_id, service_data)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        db.commit()
        return service

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        logger.error(f"Unable to update service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during service updating: {str(e)}"
        )


@service_router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
        service_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete services"
        )

    try:
        del_service = Service_Crud.delete_service(db, service_id)
        if not del_service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
        logger.info("Service deleted successfully")
        return None

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        logger.error(f"Unable to delete service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during service deletion: {str(e)}"
        )