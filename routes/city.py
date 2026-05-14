from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from utils.query_builder import apply_get_query_params

router = APIRouter(
    prefix="/cities",
    tags=["Cities"]
)


@router.post("/", response_model=schemas.CityResponse, status_code=201)
def create_city(city: schemas.CityCreate, db: Session = Depends(get_db)):
    region = db.query(models.Region).filter(
        models.Region.id_region == city.id_region
    ).first()

    if region is None:
        raise HTTPException(status_code=404, detail="Región no encontrada")

    db_city = models.City(
        name=city.name,
        id_region=city.id_region
    )

    db.add(db_city)
    db.commit()
    db.refresh(db_city)

    return db_city


@router.get("/", response_model=List[schemas.CityResponse])
def get_cities(
    query: Optional[str] = Query(
        default=None,
        description="Filter records <miembro>:<valor>"
    ),
    limit: Optional[int] = Query(
        default=None,
        ge=1,
        description="Maximum number of records to return"
    ),
    offset: Optional[int] = Query(
        default=None,
        ge=0,
        description="Number of records to skip"
    ),
    orderBy: Optional[str] = Query(
        default=None,
        description="Field used to order the results"
    ),
    sort: Optional[str] = Query(
        default="asc",
        pattern="^(asc|desc)$",
        description="Sort direction: asc or desc"
    ),
    db: Session = Depends(get_db)
):
    db_query = db.query(models.City)

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.City,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.get("/{city_id}", response_model=schemas.CityResponse)
def get_city(city_id: int, db: Session = Depends(get_db)):
    city = db.query(models.City).filter(
        models.City.id_city == city_id
    ).first()

    if city is None:
        raise HTTPException(status_code=404, detail="Ciudad no encontrada")

    return city


@router.put("/{city_id}", response_model=schemas.CityResponse)
def update_city(city_id: int, data: schemas.CityCreate, db: Session = Depends(get_db)):
    city = db.query(models.City).filter(
        models.City.id_city == city_id
    ).first()

    if city is None:
        raise HTTPException(status_code=404, detail="Ciudad no encontrada")

    region = db.query(models.Region).filter(
        models.Region.id_region == data.id_region
    ).first()

    if region is None:
        raise HTTPException(status_code=404, detail="Región no encontrada")

    city.name = data.name
    city.id_region = data.id_region

    db.commit()
    db.refresh(city)

    return city


@router.delete("/{city_id}", status_code=204)
def delete_city(city_id: int, db: Session = Depends(get_db)):
    city = db.query(models.City).filter(
        models.City.id_city == city_id
    ).first()

    if city is None:
        raise HTTPException(status_code=404, detail="Ciudad no encontrada")

    db.delete(city)
    db.commit()
