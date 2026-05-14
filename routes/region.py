from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

import DTO.models as models
import ORM.schemas as schemas
from DAO.database import get_db
from utils.query_builder import apply_get_query_params

router = APIRouter(
    prefix="/regions",
    tags=["Regions"]
)


@router.post("/", response_model=schemas.RegionResponse, status_code=201)
def create_region(region: schemas.RegionCreate, db: Session = Depends(get_db)):
    country = db.query(models.Country).filter(
        models.Country.id_country == region.id_country
    ).first()

    if country is None:
        raise HTTPException(status_code=404, detail="País no encontrado")

    db_region = models.Region(
        name=region.name,
        id_country=region.id_country
    )

    db.add(db_region)
    db.commit()
    db.refresh(db_region)

    return db_region


@router.get("/", response_model=List[schemas.RegionResponse])
def get_regions(
    query: Optional[str] = Query(
        default=None,
        description="Filter records. <miembro>:<valor>"
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
    db_query = db.query(models.Region)

    db_query = apply_get_query_params(
        db_query=db_query,
        model=models.Region,
        query=query,
        limit=limit,
        offset=offset,
        order_by=orderBy,
        sort=sort
    )

    return db_query.all()


@router.get("/{region_id}", response_model=schemas.RegionResponse)
def get_region(region_id: int, db: Session = Depends(get_db)):
    region = db.query(models.Region).filter(
        models.Region.id_region == region_id
    ).first()

    if region is None:
        raise HTTPException(status_code=404, detail="Región no encontrada")

    return region


@router.put("/{region_id}", response_model=schemas.RegionResponse)
def update_region(region_id: int, data: schemas.RegionCreate, db: Session = Depends(get_db)):
    region = db.query(models.Region).filter(
        models.Region.id_region == region_id
    ).first()

    if region is None:
        raise HTTPException(status_code=404, detail="Región no encontrada")

    country = db.query(models.Country).filter(
        models.Country.id_country == data.id_country
    ).first()

    if country is None:
        raise HTTPException(status_code=404, detail="País no encontrado")

    region.name = data.name
    region.id_country = data.id_country

    db.commit()
    db.refresh(region)

    return region


@router.delete("/{region_id}", status_code=204)
def delete_region(region_id: int, db: Session = Depends(get_db)):
    region = db.query(models.Region).filter(
        models.Region.id_region == region_id
    ).first()

    if region is None:
        raise HTTPException(status_code=404, detail="Región no encontrada")

    db.delete(region)
    db.commit()
