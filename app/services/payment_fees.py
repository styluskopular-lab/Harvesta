from decimal import Decimal, ROUND_HALF_UP

from app.models.delivery import DEFAULT_DELIVERY_FEE_UGX

SERVICE_FEE_RATE = Decimal("0.05")
VAT_ON_SERVICE_FEE_RATE = Decimal("0.18")
WALLET_WITHDRAWAL_LEVY_RATE = Decimal("0.005")
TAX_ESTIMATE_NOTE = (
    "Tax figures are configurable estimates and must be confirmed by a Ugandan tax professional."
)
_UGX = Decimal("1")


def round_ugx(amount: Decimal | float | int) -> int:
    return int(Decimal(str(amount)).quantize(_UGX, rounding=ROUND_HALF_UP))


def percentage_ugx(amount: Decimal | float | int, rate: Decimal) -> int:
    return round_ugx(Decimal(str(amount)) * rate)


def order_fee_quote(seller_subtotals: dict[int, Decimal]) -> dict:
    produce_amount = sum(seller_subtotals.values(), Decimal("0"))
    service_fee = 0
    vat = 0
    for subtotal in seller_subtotals.values():
        seller_fee = percentage_ugx(subtotal, SERVICE_FEE_RATE)
        service_fee += seller_fee
        vat += percentage_ugx(seller_fee, VAT_ON_SERVICE_FEE_RATE)

    produce_ugx = round_ugx(produce_amount)
    payable = produce_ugx + DEFAULT_DELIVERY_FEE_UGX
    return {
        "operation": "order",
        "base_amount_ugx": payable,
        "delivery_fee_ugx": DEFAULT_DELIVERY_FEE_UGX,
        "service_fee_ugx": service_fee,
        "withdrawal_levy_ugx": 0,
        "vat_ugx": vat,
        "total_tax_ugx": vat,
        "total_payable_ugx": payable,
        "net_amount_ugx": produce_ugx - service_fee - vat,
        "service_fee_payer": "farmer",
        "tax_estimate": True,
        "tax_note": TAX_ESTIMATE_NOTE,
    }


def wallet_fee_quote(operation: str, amount_ugx: int) -> dict:
    if operation == "deposit":
        service_fee = 0
        levy = 0
        vat = 0
        total_payable = amount_ugx
        net_amount = amount_ugx
    elif operation == "withdrawal":
        service_fee = 0
        levy = percentage_ugx(amount_ugx, WALLET_WITHDRAWAL_LEVY_RATE)
        vat = 0
        total_payable = amount_ugx + levy
        net_amount = amount_ugx
    else:
        raise ValueError(f"Unsupported wallet operation: {operation}")

    return {
        "operation": operation,
        "base_amount_ugx": amount_ugx,
        "delivery_fee_ugx": 0,
        "service_fee_ugx": service_fee,
        "withdrawal_levy_ugx": levy,
        "vat_ugx": vat,
        "total_tax_ugx": levy + vat,
        "total_payable_ugx": total_payable,
        "net_amount_ugx": net_amount,
        "service_fee_payer": None,
        "tax_estimate": True,
        "tax_note": TAX_ESTIMATE_NOTE,
    }
