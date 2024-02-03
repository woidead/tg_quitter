import logging
import os
import sys

import sentry_sdk
import yaml
from sentry_sdk.integrations.logging import LoggingIntegration

import config

try:
    base_path = getattr(sys, '_MEIPASS',
                        os.path.dirname(os.path.abspath(__file__)))
    dynamic_config = yaml.safe_load(
        open(os.path.join(base_path, 'build.yml'), encoding='utf-8-sig')) or {}
except:
    dynamic_config = {}

handlers = [logging.FileHandler('app.log', encoding="utf-8")]

# Check if a console is available
if sys.stdout.isatty():
    handlers.append(logging.StreamHandler())

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=handlers)

debug = False
if hasattr(config, 'debug'):
    debug = config.debug

if debug:
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler('debug.log', encoding="utf-8")
                        ])
    
class FilterTelethonDifferences(logging.Filter):
    def filter(self, record):
        return "Got difference for" not in record.getMessage() and \
        'Server sent a very old message' not in record.getMessage() and \
               'Security error while unpacking a received message' not in record.getMessage()

    
filter = FilterTelethonDifferences()

for handler in logging.getLogger().handlers:
    handler.addFilter(filter)

SENTRY_DSN = dynamic_config.get('SENTRY_DSN', '')

# Set up Sentry
sentry_sdk.init(
    dsn=SENTRY_DSN,
    integrations=[
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.WARNING
        )
    ],
    traces_sample_rate=1.0
)
