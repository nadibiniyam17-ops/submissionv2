from functools import wraps

from django.core.cache import cache


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def rate_limit(key_prefix, limit, window):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method != 'POST':
                return view(request, *args, **kwargs)
            cache_key = f'{key_prefix}:{client_ip(request)}'
            count = cache.get(cache_key, 0)
            if count >= limit:
                request.rate_limited = True
                return view(request, *args, **kwargs)
            cache.set(cache_key, count + 1, window)
            request.rate_limited = False
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
