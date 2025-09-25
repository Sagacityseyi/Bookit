import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from sqlalchemy.sql.functions import current_user
from app import models
from app.database import get_db
from app.models import Service, User
from app.schemas.service import ServiceOut, ServiceCreate, ServiceUpdate
from app.schemas.user import Role
from app.security import get_current_user



logger = logging.getLogger(__name__)

class Service:
    @staticmethod
    def get_services(
        db: Session,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100
    ):
        query = db.query(models.Service)
        logger.info("Fetching services with filters: "
                    f"price_min={price_min}, price_max={price_max}, active={active}, "
                    f"skip={skip}, limit={limit}")

        if price_min is not None:
            query = query.filter(models.Service.price >= price_min)

        if price_max is not None:
            query = query.filter(models.Service.price <= price_max)

        if active is not None:
            query = query.filter(models.Service.is_active == active)

        total = query.count()


        services = query.order_by(models.Service.created_at.desc()).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(services)} services out of {total} total matching services")

        return services, total

    @staticmethod
    def get_service(db: Session, service_id: UUID):
        logging.info(f"Checking if service exists: {service_id}")
        try:
            service = db.query(models.Service).filter(models.Service.id == service_id).first()

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
        service = models.Service(
            title=service_data.title,
            description=service_data.description,
            price = service_data.price,
            duration_minutes = service_data.duration_minutes
            )


        db.add(service)
        db.flush()
        db.refresh(service)
        return service

    @staticmethod
    def update_service(db: Session, service_id: UUID, service_data: ServiceUpdate):
        service = db.query(models.Service).filter(models.Service.id == service_id).first()
        if not service:
            return None

        update_data = service_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(service, field, value)

        db.flush()
        db.refresh(service)
        return service

        return service

    @staticmethod
    def delete_service(db: Session, service_id: UUID):
        service = db.query(models.Service).filter(models.Service.id == service_id).first()
        if not service:
            return False

        db.delete(service)
        db.commit()
        return True


Service_Crud = Service()