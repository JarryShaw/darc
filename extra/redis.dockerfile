FROM redis:alpine

# setup configuration
COPY extra/redis.conf /usr/local/etc/redis/redis.conf

# setup commands
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]
