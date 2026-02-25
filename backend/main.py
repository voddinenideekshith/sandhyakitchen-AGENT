from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import setup_logging, configure_logging
from routes import brands, menu, orders, admin_menu, auth as auth_routes, admin_orders, ai as ai_routes
from database import init_db, SessionLocal
from sqlalchemy import select
from models.user import User
from auth import get_password_hash
from core.logging import configure_logging
import logging
from services.ai import shutdown_service
from core.middleware.request_id import RequestIDMiddleware

# initialize basic logging for production readiness before app creation
setup_logging()

app = FastAPI(title=settings.APP_NAME)
# Health check endpoint (Render + monitoring)
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "sandhya-kitchen-agent"
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# attach request id middleware to populate request_id contextvar and response header
app.add_middleware(RequestIDMiddleware)


@app.on_event("startup")
async def startup_event():
    # configure structured logging first
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("application_starting")

    await init_db()
    # Validate AI provider config early so startup fails fast if secrets are missing
    if settings.AI_PROVIDER and settings.AI_PROVIDER.lower() == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY environment variable is required when AI_PROVIDER=openai")
    # ensure a default admin user exists (username/password from env or 'admin'/'admin')
    admin_user = settings.ADMIN_USERNAME
    admin_pass = settings.ADMIN_PASSWORD
    async with SessionLocal() as session:
        q = select(User).where(User.username == admin_user)
        res = await session.execute(q)
        existing = res.scalars().first()
        if not existing:
            hashed = get_password_hash(admin_pass)
            user = User(username=admin_user, hashed_password=hashed, role='admin')
            session.add(user)
            await session.commit()
            await session.refresh(user)
    logger.info("application_started")


@app.on_event("shutdown")
async def shutdown_event():
    logger = logging.getLogger(__name__)
    logger.info("application_shutting_down")
    try:
        await shutdown_service()
    except Exception:
        logger.exception("error during ai service shutdown")
    logger.info("application_shutdown_complete")


app.include_router(brands.router, prefix="/brands", tags=["brands"])
app.include_router(menu.router, prefix="/menu", tags=["menu"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(admin_menu.router, prefix="/admin/menu", tags=["admin_menu"])
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(admin_orders.router, prefix="/admin/orders", tags=["admin_orders"])
app.include_router(ai_routes.router, prefix="/ai", tags=["ai"])


@app.get("/", tags=["health"])
def health_check():
    return {"status": "Sandhya Kitchen API running"}


@app.get("/health")
def readiness():
    return {"ok": True}