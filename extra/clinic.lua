-- EVAL

local keys = redis.call('zrangebyscore', KEYS[1], ARGV[1], ARGV[2])

local start = 1
while start <= #keys do
    -- chunked by 5,000 keys
    redis.call("del", unpack(keys, start, math.min(start+4999, #keys)))
    start = start + 5000
end

return redis.status_reply("ok")

-- 1 key min max
