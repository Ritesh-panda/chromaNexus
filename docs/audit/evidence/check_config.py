import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.app.core.config import settings
from backend.app.core.database import SQLALCHEMY_DATABASE_URL

print("Config DATABASE_URL:", getattr(settings, "DATABASE_URL", None))
print("Resolved SQLALCHEMY_DATABASE_URL:", SQLALCHEMY_DATABASE_URL)
