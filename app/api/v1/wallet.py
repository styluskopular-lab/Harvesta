from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.schemas.wallet import (
    FeeBreakdown,
    WalletDepositCreate,
    WalletOverview,
    WalletQuoteRequest,
    WalletTransactionAdminRead,
    WalletTransactionDecision,
    WalletTransactionRead,
    WalletWithdrawalCreate,
)
from app.services.notification_dispatcher import dispatch_user_notification
from app.services.payment_fees import wallet_fee_quote
from app.services.wallet import wallet_balance_ugx

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/", response_model=WalletOverview)
def get_wallet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transactions = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.user_id == current_user.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(50)
        .all()
    )
    return WalletOverview(
        balance_ugx=wallet_balance_ugx(db, current_user.id),
        transactions=transactions,
    )


@router.post("/quote", response_model=FeeBreakdown)
def quote_wallet_operation(
    quote_in: WalletQuoteRequest,
    current_user: User = Depends(get_current_user),
):
    return wallet_fee_quote(quote_in.operation, quote_in.amount_ugx)


@router.post("/deposits", response_model=WalletTransactionRead, status_code=201)
def request_deposit(
    deposit_in: WalletDepositCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quote = wallet_fee_quote("deposit", deposit_in.amount_ugx)
    transaction = WalletTransaction(
        user_id=current_user.id,
        transaction_type="deposit",
        amount_ugx=deposit_in.amount_ugx,
        balance_delta_ugx=quote["net_amount_ugx"],
        status="pending",
        payment_method=deposit_in.payment_method,
        reference=deposit_in.reference.strip() if deposit_in.reference else None,
        description=(
            f"Pending {deposit_in.payment_method.replace('_', ' ')} wallet deposit; "
            "credit is held until an administrator verifies the payment"
        ),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    dispatch_user_notification(
        db,
        current_user,
        "wallet_deposit_pending",
        "Harvesta Wallet deposit pending",
        (
            f"Your UGX {deposit_in.amount_ugx:,} deposit is pending verification. "
            "It has not been credited to your wallet."
        ),
    )
    return transaction


@router.post("/withdrawals", response_model=WalletTransactionRead, status_code=201)
def request_withdrawal(
    withdrawal_in: WalletWithdrawalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(User.id).filter(User.id == current_user.id).with_for_update().first()
    quote = wallet_fee_quote("withdrawal", withdrawal_in.amount_ugx)
    balance = wallet_balance_ugx(db, current_user.id)
    if balance < quote["total_payable_ugx"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient wallet funds. Available: UGX {balance:,}; "
                f"required: UGX {quote['total_payable_ugx']:,}, including the "
                "estimated withdrawal levy."
            ),
        )

    transaction = WalletTransaction(
        user_id=current_user.id,
        transaction_type="withdrawal",
        amount_ugx=withdrawal_in.amount_ugx,
        tax_amount_ugx=quote["withdrawal_levy_ugx"],
        balance_delta_ugx=-quote["total_payable_ugx"],
        status="pending",
        payment_method="mobile_money",
        destination=withdrawal_in.destination.strip(),
        description=(
            "Pending withdrawal; requested amount plus estimated levy is reserved "
            "until an administrator processes the payout"
        ),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    dispatch_user_notification(
        db,
        current_user,
        "wallet_withdrawal_pending",
        "Harvesta Wallet withdrawal pending",
        (
            f"Your UGX {withdrawal_in.amount_ugx:,} withdrawal request is pending. "
            "The amount and estimated levy are reserved until processed."
        ),
    )
    return transaction


@router.get("/admin/pending", response_model=list[WalletTransactionAdminRead])
def list_pending_wallet_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    return (
        db.query(WalletTransaction)
        .filter(WalletTransaction.status == "pending")
        .order_by(WalletTransaction.created_at.asc())
        .all()
    )


@router.patch(
    "/admin/transactions/{transaction_id}",
    response_model=WalletTransactionAdminRead,
)
def resolve_wallet_transaction(
    transaction_id: int,
    decision: WalletTransactionDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    transaction = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.id == transaction_id)
        .with_for_update()
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Wallet transaction not found")
    if transaction.status != "pending":
        raise HTTPException(status_code=409, detail="Wallet transaction is already resolved")

    transaction.status = decision.status
    transaction.resolved_at = datetime.now(timezone.utc)
    if decision.reference is not None:
        transaction.reference = decision.reference.strip() or transaction.reference
    if decision.status == "rejected":
        transaction.description = f"{transaction.description}; rejected by administrator"
    else:
        transaction.description = f"{transaction.description}; processed by administrator"
    db.commit()
    db.refresh(transaction)

    user = (
        db.query(User)
        .filter(User.id == transaction.user_id)
        .first()
        if transaction.user_id is not None
        else None
    )
    if user:
        dispatch_user_notification(
            db,
            user,
            f"wallet_{transaction.transaction_type}_{decision.status}",
            f"Harvesta Wallet {transaction.transaction_type} {decision.status}",
            (
                f"Your UGX {transaction.amount_ugx:,} "
                f"{transaction.transaction_type} has been {decision.status}."
            ),
        )
    return transaction
