import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from sqlalchemy.sql.functions import current_user

from app.database import get_db
from app.models import Service, User
from app.schemas.service import ServiceOut, ServiceCreate, ServiceUpdate
from app.schemas.user import Role
from app.security import get_current_user


logger = logging.getLogger(__name__)

class Service:
    @staticmethod
    def get_services(
        db: Session = Depends(get_db),
        q: Optional[str] = Query(None, description="Search query for title or description"),
        price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
        price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
        active: Optional[bool] = Query(True, description="Filter by active status")
):
     query = db.query(Service)

     if q:
        query = query.filter(
            (Service.title.ilike(f"%{q}%")) |
            (Service.description.ilike(f"%{q}%"))
        )
     if price_min is not None:
        query = query.filter(Service.price >= price_min)

     if price_max is not None:
        query = query.filter(Service.price <= price_max)

     if active is not None:
        query = query.filter(Service.is_active == active)

     services = query.order_by(Service.created_at.desc()).all()
     return services

    @staticmethod
    def get_service(db: Session, service_id: UUID):
        logging.info(f"Checking if service exists: {service_id}")
        try:
            service = db.query(Service).filter(Service.id == service_id).first()

            if not service:
                logging.warning(f"Service not found: {service_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Service not found"
                )

            if not service.is_active:
                logging.warning(f"Service is inactive: {service_id}")
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Service is not available"
                )
            logging.info(f"Service found: {service_id}")
            return service

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Error retrieving service {service_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving service: {str(e)}"
            )

    @staticmethod
    def create_service(db: Session, service_data: ServiceCreate):
        logging.info()
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


Service_Crud = Service()