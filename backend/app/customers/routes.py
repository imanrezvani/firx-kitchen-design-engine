from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentContext, get_tenant_db, resolve_context
from app.projects.models import Customer
from app.schemas import CustomerCreate, CustomerOut, CustomerUpdate

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.get("", response_model=list[CustomerOut])
async def list_customers(
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    return (await db.execute(select(Customer).order_by(Customer.created_at.desc()))).scalars().all()


@router.post("", response_model=CustomerOut, status_code=201)
async def create_customer(
    body: CustomerCreate,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    customer = Customer(**body.model_dump())
    db.add(customer)
    await db.flush()
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, detail="customer_not_found")
    return customer


@router.put("/{customer_id}", response_model=CustomerOut)
async def update_customer(
    customer_id: str,
    body: CustomerUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, detail="customer_not_found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(customer, k, v)
    await db.flush()
    return customer


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    _ctx: CurrentContext = Depends(resolve_context),
):
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, detail="customer_not_found")
    await db.delete(customer)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            409,
            detail="این مشتری دارای پروژه است و قابل حذف نیست.",
        )
