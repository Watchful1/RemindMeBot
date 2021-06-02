import discord_logging
from datetime import timedelta
import requests
import time

log = discord_logging.init_logging()

import utils

USER_AGENT = "Pushshift tester by u/Watchful1"
BETA_START = utils.datetime_from_timestamp(1622071192)
START_TIME = utils.datetime_now()
PROD_START = None

while True:
    url = "https://api.pushshift.io/reddit/comment/search"
    comments = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=10).json()['data']
    comment_time = utils.datetime_from_timestamp(comments[0]['created_utc'])

    if PROD_START is None:
        PROD_START = comment_time

    change_from_prod_start = comment_time - PROD_START
    seconds_since_start = utils.datetime_now() - START_TIME
    ratio = (change_from_prod_start).seconds / (seconds_since_start).seconds
    if ratio > 0:
        catchup_seconds = (BETA_START - comment_time).seconds / ratio
    else:
        catchup_seconds = 1

    log.info(f"{utils.get_datetime_string(comment_time)} - {utils.get_datetime_string(BETA_START)} : "
             f"{BETA_START - comment_time} : {change_from_prod_start} : {seconds_since_start} | "
             f"{ratio:.2} | {catchup_seconds} : {timedelta(seconds=catchup_seconds)}")
    time.sleep(10)
