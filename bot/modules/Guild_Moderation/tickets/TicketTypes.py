from enum import Enum

_type_map = {}


class TicketType(Enum):
    """
    Identifier for the different types of tickets
    """
    NOTE = 0
    MUTE = 1
    BAN = 2
    HACKBAN = 3
    KICK = 4

    @property
    def Ticket(self):
        return _type_map[self.value]


def describes_ticket(ttype: TicketType):
    """
    Decorator designating a Ticket child as the manager for a given TicketType.
    """
    def wrapper(cls):
        cls._ticket_type = ttype
        _type_map[ttype.value] = cls
        return cls
    return wrapper
