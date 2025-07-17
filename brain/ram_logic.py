import time
from collections import OrderedDict

class RAMCache:
    def __init__(self, max_size=1000, ttl_seconds=600):
        """
        :param max_size: Maximum number of items in RAM cache
        :param ttl_seconds: Time-to-live for each entry in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()  # key -> (value, timestamp)

    def _evict_if_needed(self):
        while len(self.cache) > self.max_size:
            evicted_key, _ = self.cache.popitem(last=False)
            print(f"[ram_logic] Evicted oldest cache entry: {evicted_key}")

    def _is_expired(self, timestamp):
        return (time.time() - timestamp) > self.ttl_seconds

    def set(self, key, value):
        now = time.time()
        if key in self.cache:
            self.cache.pop(key)
        self.cache[key] = (value, now)
        self._evict_if_needed()

    def get(self, key):
        if key not in self.cache:
            return None
        value, timestamp = self.cache[key]
        if self._is_expired(timestamp):
            print(f"[ram_logic] Cache entry expired: {key}")
            self.cache.pop(key)
            return None
        # Refresh position to mark as recently used
        self.cache.move_to_end(key)
        return value

    def delete(self, key):
        if key in self.cache:
            self.cache.pop(key)

    def clear(self):
        self.cache.clear()

    def keys(self):
        return list(self.cache.keys())

    def __len__(self):
        return len(self.cache)
