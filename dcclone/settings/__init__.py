import os
try:
    if os.getenv("DJANGO_STAGE") == "production":
        from .production import *
    else:
        from dotenv import load_dotenv
        load_dotenv()  # loads the configs from .env
        from .dev import *
except ImportError:
    from .dev import *
