import redis
import logging
import os

DEBUG = 0

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)
if DEBUG:
    log.setLevel(logging.DEBUG)


num_of_dock = 16
if num_of_dock > 16:
    num_of_dock += 1

redis_instance = redis.StrictRedis(
                    host='localhost',
                    port=6379,
                    db=0,
                    password='9ff7b9d0-891b-4980-8559-6a67a76a73ac'
                )

MPPT_TYPE = "mppt-epveper"
# MPPT_TYPE = "mppt-srne"

if redis_instance.get("PANEL2_TYPE"):
    PANEL2_TYPE = str(redis_instance.get("PANEL2_TYPE"))[2:-1]
else:
    # PANEL2_TYPE = "new"
    PANEL2_TYPE = "old"

try:
    if MPPT_TYPE == "mppt-srne" and PANEL2_TYPE == "new":
        number_mppt = [int(redis_instance.get('mppt:1:id')), int(redis_instance.get('mppt:2:id')), int(redis_instance.get('mppt:3:id'))]
    elif MPPT_TYPE == "mppt-srne" and PANEL2_TYPE == "old":
        number_mppt = [1,2,3]
    elif MPPT_TYPE == "mppt-epveper":
        number_mppt = [1,2]
except TypeError:
    number_mppt = [1,2,3]