import json
import os

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from flags.service import is_enabled

from .models import Order
from .pricing import discount_cents, discount_cents_v2
from .services import InvalidOrder, place_order


@require_GET
def healthz(request):
    """Liveness: the process can answer. Never touches the database."""
    return JsonResponse({"status": "ok"})


@require_GET
def readyz(request):
    """Readiness: send me traffic? No while draining, or when the database is unreachable."""
    if os.path.exists(settings.DRAIN_FILE):
        return JsonResponse({"status": "draining"}, status=503)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "db-unavailable"}, status=503)
    return JsonResponse({"status": "ready"})


@require_GET
def version(request):
    return JsonResponse({"version": settings.APP_VERSION, "sha": settings.GIT_SHA})


def _order_json(order):
    return {
        "id": str(order.id),
        "customer_email": order.customer_email,
        "status": order.status,
        "total_cents": order.total_cents(),
    }


@csrf_exempt  # JSON API without cookie auth in this lab; see 012 ch06 for CSRF on session-authenticated APIs
@require_http_methods(["GET", "POST"])
def orders(request):
    if request.method == "GET":
        recent = Order.objects.prefetch_related("lines").order_by("-created_at")[:20]
        return JsonResponse({"data": [_order_json(o) for o in recent]})
    try:
        body = json.loads(request.body)
        order = place_order(body["customer_email"], body["items"])
    except (ValueError, KeyError, TypeError) as exc:
        message = str(exc) if isinstance(exc, InvalidOrder) else "invalid body"
        return JsonResponse({"error": message}, status=422)
    return JsonResponse(_order_json(order), status=201)


@require_GET
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("lines"), pk=order_id)
    return JsonResponse(_order_json(order))


@require_GET
def quote(request):
    """Discount quote. Pricing v2 is behind the new_pricing flag: deployed dark, released per customer."""
    try:
        customer, total = request.GET["customer"], int(request.GET["total_cents"])
    except KeyError, ValueError:
        return JsonResponse({"error": "customer and total_cents are required"}, status=422)
    if is_enabled("new_pricing", customer):
        engine, discount = "v2", discount_cents_v2(total)
    else:
        engine, discount = "v1", discount_cents(total)
    return JsonResponse({"customer": customer, "total_cents": total, "discount_cents": discount, "engine": engine})
