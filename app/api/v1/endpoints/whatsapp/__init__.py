from . import messages, groups, instances, webhooks

router = APIRouter()

router.include_router(instances.router, prefix="/instance", tags=["WhatsApp Instance Management"])
router.include_router(messages.router, prefix="/messages", tags=["WhatsApp Messaging"])
router.include_router(groups.router, prefix="/groups", tags=["WhatsApp Group Management"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["WhatsApp Webhooks"])
