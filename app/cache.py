import time

cached_data = None
cached_at = None
TTL = 3600 #seconds

def get_cached_rankings():
    global cached_data
    global cached_at
    if cached_data is None:
        return None
    
    if time.time() - cached_at > TTL:
        return None #expired
    
    return cached_data


def set_cached_rankings(data):
    global cached_data 
    global cached_at 
    cached_data = data
    cached_at = time.time()
