import redis
from django.conf import settings
from rest_framework.throttling import UserRateThrottle

REDIS_POOL = redis.ConnectionPool.from_url(settings.CELERY_BROKER_URL, max_connections=50)

class CheckoutRateThrottle(UserRateThrottle):

    def parse_rate(self, rate):
        if rate is None:
            return (None, None)
        try:
            num, period = rate.split('/')
            num_requests = int(num)
            if period.endswith('s') and period[:-1].isdigit():
                duration = int(period[:-1])
                return (num_requests, duration)
        except (ValueError, IndexError):
            pass
        return super().parse_rate(rate)

    def get_rate(self):
        try:
            redis_conn = redis.Redis(connection_pool=REDIS_POOL)
            queue_length = redis_conn.llen('celery')

            if queue_length > 400   :
                print(f"[DYNAMIC THROTTLE] Heavy Load! Rate dropped to 1/25s (Queue: {queue_length})")
                return '1/25s'
            elif queue_length > 250:
                print(f"[DYNAMIC THROTTLE] Medium Load! Rate adjusted to 3/25s (Queue: {queue_length})")
                return '3/25s'
            else:
                return '15/25s'
        except Exception as e:
            print(f"Error in dynamic throttle, falling back to static rate: {str(e)}")
            return '5/25s'