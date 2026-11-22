from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.farm_finance import FarmTransaction
from app.schemas.farm_finance import FarmTransactionCreate, FarmTransactionRead

router = APIRouter(prefix="/farm-finance", tags=["Farm Finance"])


@router.post("/transactions", response_model=FarmTransactionRead, status_code=201)
def create_transaction(
    payload: FarmTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"farmer", "admin"}:
        raise HTTPException(status_code=403, detail="Only farmers can manage farm finances")
    transaction = FarmTransaction(owner_id=current_user.id, **payload.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/transactions", response_model=list[FarmTransactionRead])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(FarmTransaction).filter(
        FarmTransaction.owner_id == current_user.id
    ).order_by(FarmTransaction.transaction_date.desc()).all()


@router.get("/summary")
def finance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transactions = db.query(FarmTransaction).filter(
        FarmTransaction.owner_id == current_user.id
    ).all()
    revenue = sum(t.amount for t in transactions if t.transaction_type == "income")
    cost = sum(t.amount for t in transactions if t.transaction_type == "expense")
    profit = revenue - cost
    margin = (profit / revenue * 100) if revenue else 0.0
    monthly = defaultdict(lambda: {"revenue": 0.0, "cost": 0.0})
    budget = defaultdict(float)
    for transaction in transactions:
        month = transaction.transaction_date.strftime("%Y-%m")
        if transaction.transaction_type == "income":
            monthly[month]["revenue"] += transaction.amount
        else:
            monthly[month]["cost"] += transaction.amount
            budget[transaction.category] += transaction.amount
    return {
        "total_revenue": revenue,
        "total_cost": cost,
        "gross_profit": profit,
        "gross_margin": round(margin, 2),
        "monthly": [
            {"month": month, "revenue": values["revenue"], "cost": values["cost"]}
            for month, values in sorted(monthly.items())
        ],
        "budget_breakdown": [
            {"category": category, "amount": amount}
            for category, amount in sorted(budget.items(), key=lambda item: item[1], reverse=True)
        ],
    }


@router.delete("/transactions/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = db.query(FarmTransaction).filter(FarmTransaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if transaction.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(transaction)
    db.commit()
    return None
