from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.db_models import Service, User
from app.models.schemas import GeoPoint, ServiceCreate, ServiceOut, ServiceStatusUpdate
from app.services import services_repository as repo

router = APIRouter(prefix="/services", tags=["services"])


def _to_out(service: Service, distance_km: Optional[float] = None) -> ServiceOut:
    return ServiceOut(
        id=service.id,
        owner_uid=service.owner_id,
        owner_name=service.owner_name,
        owner_phone=service.owner_phone,
        title=service.title,
        description=service.description,
        category=service.category,
        price_amd=service.price_amd,
        location=GeoPoint(lat=service.lat, lng=service.lng),
        created_at=service.created_at,
        distance_km=distance_km,
        is_active=service.is_active,
    )


@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = repo.create_service(db, current_user, payload)
    return _to_out(service)


@router.get("", response_model=list[ServiceOut])
def browse_services(
    category: Optional[str] = None,
    search: Optional[str] = Query(None, description="Searches title + description"),
    lat: Optional[float] = Query(None, description="Your latitude, for nearby search"),
    lng: Optional[float] = Query(None, description="Your longitude, for nearby search"),
    radius_km: float = Query(15.0, gt=0, le=100),
    limit: int = Query(50, gt=0, le=100),
    db: Session = Depends(get_db),
):
    """Public browse endpoint — no auth needed, so people can see
    listings before signing in. `search` is applied together with
    `category` (AND, not OR): searching inside a category only searches
    that category. Only active (non-paused) listings are returned."""
    near = (lat, lng) if lat is not None and lng is not None else None
    pairs = repo.list_services(
        db, category=category, search=search, near=near, radius_km=radius_km, limit=limit
    )
    return [_to_out(service, distance) for service, distance in pairs]


@router.get("/mine", response_model=list[ServiceOut])
def my_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """All of the signed-in user's own listings — active and paused
    alike. Must be declared before /{service_id} below, or FastAPI would
    try to match "mine" as a service_id path parameter instead."""
    services = repo.list_my_services(db, current_user.id)
    return [_to_out(service) for service in services]


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(service_id: str, db: Session = Depends(get_db)):
    service = repo.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return _to_out(service)


@router.patch("/{service_id}", response_model=ServiceOut)
def update_service_status(
    service_id: str,
    payload: ServiceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pauses or reactivates a listing without deleting it — owner-only."""
    service = repo.set_active_status(db, service_id, current_user.id, payload.is_active)
    if service is None:
        raise HTTPException(status_code=403, detail="Not found or you don't own this listing")
    return _to_out(service)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = repo.delete_service(db, service_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=403, detail="Not found or you don't own this listing")
