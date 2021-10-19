import functools
from enum import Enum, unique


@functools.total_ordering
class OrderedEnum(Enum):
    @classmethod
    @functools.lru_cache(None)
    def _member_list(cls):
        return list(cls)

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            member_list = self.__class__._member_list()
            return member_list.index(self) < member_list.index(other)
        return NotImplemented


@unique
class DataRole(OrderedEnum):
    NO_ACCESS = "no-access"
    VIEW = "view"
    EDIT = "edit"


@unique
class AdminRole(OrderedEnum):
    NOT_ADMIN = "not-admin"
    EDIT_ACCESS = "edit-access"
    EDIT_ADMINS = "edit-admins"
