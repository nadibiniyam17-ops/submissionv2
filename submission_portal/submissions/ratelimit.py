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
            if cache.add(cache_key, 1, window):
                count = 1
            else:
                try:
                    count = cache.incr(cache_key)
                except ValueError:
                    cache.set(cache_key, 1, window)
                    count = 1
            request.rate_limited = count > limit
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
