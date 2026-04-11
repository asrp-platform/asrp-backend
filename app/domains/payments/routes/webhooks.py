import stripe
from fastapi import APIRouter, Header, HTTPException
from starlette.requests import Request

from app.core.config import settings
from app.domains.payments.use_cases.confirm_payment import ConfirmPaymentUseCaseDep

stripe.api_key = settings.STRIPE_API_KEY


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    confirm_payment_use_case: ConfirmPaymentUseCaseDep,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    payload = await request.body()

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]

    if event_type == "payment_intent.succeeded":
        await confirm_payment_use_case.execute(event)

    if event_type == "payment_intent.failed":
        # Тут обрабатываем неуспешную попытку оплаты
        pass

    if event_type == "checkout.session.completed":
        pass
        # Здесь выдаем membership (продукт)
        # session = data_object

    # Что пришло:
    # 1. payment_intent.succeeded
    # 2. checkout.session.completed

    # if event_type == "checkout.session.completed":
    #     session = data_object
    #
    #     # Обычно берут order_id из metadata или client_reference_id
    #     order_id = session.get("metadata", {}).get("order_id") or session.get("client_reference_id")
    #     payment_status = session.get("payment_status")  # usually "paid" for successful payment
    #     payment_intent_id = session.get("payment_intent")
    #     customer_id = session.get("customer")
    #
    #     # 1. найти заказ в БД
    #     # 2. проверить, что он еще не помечен как paid
    #     # 3. отметить заказ как paid / fulfilled
    #     # 4. сохранить payment_intent_id, customer_id, event id и т.д.
    #
    #     print("Checkout completed", {
    #         "order_id": order_id,
    #         "payment_status": payment_status,
    #         "payment_intent_id": payment_intent_id,
    #         "customer_id": customer_id,
    #     })
    #
    # elif event_type == "checkout.session.async_payment_succeeded":
    #     session = data_object
    #     order_id = session.get("metadata", {}).get("order_id") or session.get("client_reference_id")
    #
    #     # Помечаем заказ как успешно оплаченный
    #     print("Async payment succeeded", {"order_id": order_id})
    #
    # elif event_type == "checkout.session.async_payment_failed":
    #     session = data_object
    #     order_id = session.get("metadata", {}).get("order_id") or session.get("client_reference_id")
    #
    #     # Помечаем заказ как failed / awaiting_new_payment
    #     print("Async payment failed", {"order_id": order_id})
    #
    # elif event_type == "payment_intent.succeeded":
    #     payment_intent = data_object
    #     print("PaymentIntent succeeded", {
    #         "payment_intent_id": payment_intent.get("id"),
    #         "amount": payment_intent.get("amount"),
    #     })
    #
    # elif event_type == "payment_intent.payment_failed":
    #     payment_intent = data_object
    #     print("PaymentIntent failed", {
    #         "payment_intent_id": payment_intent.get("id"),
    #     })
    #
    # return JSONResponse({"received": True})
