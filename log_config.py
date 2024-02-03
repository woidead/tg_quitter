import logging
import sys

handlers = [logging.FileHandler('app.log', encoding="utf-8")]

# Check if a console is available
if sys.stdout.isatty():
    handlers.append(logging.StreamHandler())

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=handlers)

    
class FilterTelethonDifferences(logging.Filter):
    def filter(self, record):
        return "Got difference for" not in record.getMessage() and \
        'Server sent a very old message' not in record.getMessage() and \
               'Security error while unpacking a received message' not in record.getMessage()

    
filter = FilterTelethonDifferences()

for handler in logging.getLogger().handlers:
    handler.addFilter(filter)
