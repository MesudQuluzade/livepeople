import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "livepeople.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

# Prepare the writable serverless database on a cold start. This keeps login
# and registration from failing with SQLite's read-only filesystem error.
if os.environ.get("VERCEL"):
    from pathlib import Path
    from django.conf import settings
    from django.core.management import call_command
    from django.contrib.auth import get_user_model

    database_path = Path(settings.DATABASES["default"]["NAME"])
    if not database_path.exists():
        call_command("migrate", interactive=False, verbosity=0)
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                password=settings.ADMIN_ACCESS_PASSWORD,
                email="",
            )
