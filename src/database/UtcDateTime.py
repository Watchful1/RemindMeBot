import sqlalchemy.types as types

import utils


class UtcDateTime(types.TypeDecorator):
    impl = types.DateTime

    cache_ok = True

    def process_result_value(self, value, dialect):
        return utils.datetime_force_utc(value)
