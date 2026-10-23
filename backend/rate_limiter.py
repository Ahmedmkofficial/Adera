from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory limits are suitable for a single-process demo only.
limiter = Limiter(key_func=get_remote_address)
