import secrets

from django.db import migrations
from django.db.models import Q


def build_token():
    return secrets.token_urlsafe(12).replace("-", "").replace("_", "").lower()[:20]


def populate_tracking_tokens(apps, schema_editor):
    Pedido = apps.get_model("MainApp", "Pedido")
    for pedido in Pedido.objects.filter(Q(tracking_token__isnull=True) | Q(tracking_token="")):
        token = build_token()
        while Pedido.objects.filter(tracking_token=token).exists():
            token = build_token()
        pedido.tracking_token = token
        pedido.save(update_fields=["tracking_token"])


class Migration(migrations.Migration):
    dependencies = [
        ("MainApp", "0002_pedido_estado_pago_pedido_mensaje_pago_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_tracking_tokens, migrations.RunPython.noop),
    ]
