# Threaded Logging Object ---- To be used by multiple sources
import logging

# Global Logging Object
logging.basicConfig(filename="../log/server.log", format='%(asctime)s %(message)s', filemode='a')
logger = logging.getLogger()


