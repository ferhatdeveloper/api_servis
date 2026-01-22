from loguru import logger
import sys
import os

# Define log paths
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def configure_logging():
    """
    Configures the advanced logging system using Loguru.
    - Console: Info level (Concise)
    - App File: Info level (Rotating)
    - Error File: Error level (Rotating, Backtrace, Diagnose)
    - Integration File: Filtered stream for Logo/ERP logs
    """
    # Remove default handler
    logger.remove()

    # 1. Console Handler (Development Friendly)
    logger.add(
        sys.stdout, 
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO",
        enqueue=True
    )

    # 2. General Application Log (Everything INFO+)
    logger.add(
        os.path.join(LOG_DIR, "exfin.log"), 
        rotation="10 MB", 
        retention="10 days", 
        compression="zip",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
        backtrace=True,
        diagnose=True
    )

    # 3. Dedicated Error Log (ONLY ERROR+) - Keeping it clean for debugging
    logger.add(
        os.path.join(LOG_DIR, "error.log"), 
        rotation="5 MB", 
        retention="30 days",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        enqueue=True,
        backtrace=True,  # Full stack trace
        diagnose=True    # Show variable values in stack trace (Use CAREFULLY in production w/ sensitive data)
    )

    # 4. Logo / Integration Log
    logger.add(
        os.path.join(LOG_DIR, "logo.log"), 
        filter=lambda record: "logo" in record["name"].lower() or "integration" in record["message"].lower(),
        rotation="10 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} - {message}",
        enqueue=True
    )

    # 5. Retail Log
    logger.add(
        os.path.join(LOG_DIR, "retail.log"), 
        filter=lambda record: "retail" in record["name"].lower(),
        rotation="10 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} - {message}",
        enqueue=True
    )

    # 6. PDKS Log
    logger.add(
        os.path.join(LOG_DIR, "pdks.log"), 
        filter=lambda record: "pdks" in record["name"].lower(),
        rotation="5 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} - {message}",
        enqueue=True
    )

    # 7. Analytics/Reports Log
    logger.add(
        os.path.join(LOG_DIR, "analytics.log"), 
        filter=lambda record: "analytics" in record["name"].lower() or "reports" in record["name"].lower(),
        rotation="5 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} - {message}",
        enqueue=True
    )


    logger.info("Advanced Logging System Initialized 🚀")
