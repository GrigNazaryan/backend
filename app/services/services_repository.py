from typing import Optional

from geopy.distance import geodesic
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.db_models import Service, User
from app.models.schemas import ServiceCreate


def create_service(db: Session, owner: User, payload: ServiceCreate) -> Service:
    if payload.owner_name and owner.display_name in ("Unnamed user", ""):
        owner.display_name = payload.owner_name
    if payload.owner_phone and not owner.phone_number:
        owner.phone_number = payload.owner_phone

    service = Service(
        owner_id=owner.id,
        owner_name=payload.owner_name or owner.display_name,
        owner_phone=payload.owner_phone or owner.phone_number,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        price_amd=payload.price_amd,
        lat=payload.location.lat,
        lng=payload.location.lng,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def list_services(
    db: Session,
    category: Optional[str] = None,
    search: Optional[str] = None,
    near: Optional[tuple[float, float]] = None,
    radius_km: float = 15.0,
    limit: int = 50,
) -> list[tuple[Service, Optional[float]]]:
    """Lists services, applying category filter and text search together
    (AND, not OR) — searching while a category is selected only searches
    within that category, never escapes it.

    Only active listings are returned here — paused ones are only
    visible to their owner via list_my_services.

    Returns (service, distance_km) pairs; distance_km is None whenever
    `near` wasn't provided.
    """
    query = select(Service).where(Service.is_active.is_(True))

    if category:
        query = query.where(Service.category == category)

    if search:
        pattern = f"%{search.strip()}%"
        # ilike = case-insensitive LIKE, native to Postgres.
        query = query.where(or_(Service.title.ilike(pattern), Service.description.ilike(pattern)))

    query = query.order_by(Service.created_at.desc())
    if not near:
        query = query.limit(limit)

    results = list(db.execute(query).scalars().all())

    if not near:
        return [(service, None) for service in results]

    annotated: list[tuple[float, Service]] = []
    for service in results:
        distance = geodesic(near, (service.lat, service.lng)).km
        if distance <= radius_km:
            annotated.append((distance, service))
    annotated.sort(key=lambda pair: pair[0])

    return [(service, round(distance, 2)) for distance, service in annotated[:limit]]


def list_my_services(db: Session, owner_id: str) -> list[Service]:
    """All of a user's own listings, active and paused alike — this is
    the one place paused listings are still visible, so an owner can
    reactivate or delete them."""
    query = select(Service).where(Service.owner_id == owner_id).order_by(Service.created_at.desc())
    return list(db.execute(query).scalars().all())


def set_active_status(db: Session, service_id: str, owner_id: str, is_active: bool) -> Optional[Service]:
    service = db.get(Service, service_id)
    if service is None or service.owner_id != owner_id:
        return None
    service.is_active = is_active
    db.commit()
    db.refresh(service)
    return service


def get_service(db: Session, service_id: str) -> Optional[Service]:
    return db.get(Service, service_id)


def delete_service(db: Session, service_id: str, owner_id: str) -> bool:
    service = db.get(Service, service_id)
    if service is None or service.owner_id != owner_id:
        return False
    db.delete(service)
    db.commit()
    return True
