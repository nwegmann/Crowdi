from .auth import router as auth_router
from .homepage import router as homepage_router
from .items import router as items_router
from .requests import router as requests_router
from .conversations import router as conversations_router
from .notifications import router as notifications_router

routers = [
    auth_router,
    homepage_router,
    items_router,
    requests_router,
    conversations_router,
    notifications_router
]