from enum import Enum


class ReturnType(Enum):
	INVALID_USER = 1
	THREAD_LOCKED = 2
	FORBIDDEN = 3
	USER_DOESNT_EXIST = 4
