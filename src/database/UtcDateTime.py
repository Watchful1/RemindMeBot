import sqlalchemy.types as types

import utils


class UtcDateTime(types.TypeDecorator):
    impl = types.DateTime

    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None:
            return utils.datetime_force_utc(value)
        else:
            return None
