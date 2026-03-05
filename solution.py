## Student Name: Cyrus Yang
## Student ID: 219583038

"""
Task B: Event Registration with Waitlist (Stub)
In this lab, you will design and implement an Event Registration with Waitlist system using an LLM assistant as your primary programming collaborator. 
You are asked to implement a Python module that manages registration for a single event with a fixed capacity. 
The system must:
•	Accept a fixed capacity.
•	Register users until capacity is reached.
•	Place additional users into a FIFO waitlist.
•	Automatically promote the earliest waitlisted user when a registered user cancels.
•	Prevent duplicate registrations.
•	Allow users to query their current status.

The system must ensure that:
•	The number of registered users never exceeds capacity.
•	Waitlist ordering preserves FIFO behavior.
•	Promotions occur deterministically under identical operation sequences.

The module must preserve the following invariants:
•	A user may not appear more than once in the system.
•	A user may not simultaneously exist in multiple states.
•	The system state must remain consistent after every operation.

The system must correctly handle non-trivial scenarios such as:
•	Multiple cancellations in sequence.
•	Users attempting to re-register after canceling.
•	Waitlisted users canceling before promotion.
•	Capacity equal to zero.
•	Simultaneous or rapid consecutive operations.
•	Queries during state transitions.

The output consists of the updated registration state and ordered lists of registered and waitlisted users after each operation.
"""

from dataclasses import dataclass
from typing import List, Optional
from collections import deque


class DuplicateRequest(Exception):
    """Raised if a user tries to register but is already registered or waitlisted."""
    pass


class NotFound(Exception):
    """Raised if a user cannot be found for cancellation."""
    pass


@dataclass(frozen=True)
class UserStatus:
    state: str
    position: Optional[int] = None


class EventRegistration:

    def __init__(self, capacity: int) -> None:
        if capacity < 0:
            raise ValueError("capacity must be >= 0")

        self.capacity = capacity
        self.registered: List[str] = []
        self.waitlist = deque()

        # used to enforce uniqueness
        self.all_users = set()

    def register(self, user_id: str) -> UserStatus:

        if user_id in self.all_users:
            raise DuplicateRequest(f"{user_id} already registered or waitlisted")

        # capacity available
        if len(self.registered) < self.capacity:
            self.registered.append(user_id)
            self.all_users.add(user_id)
            return UserStatus("registered")

        # capacity full → waitlist
        self.waitlist.append(user_id)
        self.all_users.add(user_id)

        position = len(self.waitlist)
        return UserStatus("waitlisted", position)

    def cancel(self, user_id: str) -> None:

        if user_id not in self.all_users:
            raise NotFound(f"{user_id} not found")

        # cancel registered user
        if user_id in self.registered:
            self.registered.remove(user_id)
            self.all_users.remove(user_id)

            # promote earliest waitlisted user
            if self.waitlist:
                promoted = self.waitlist.popleft()
                self.registered.append(promoted)

        else:
            # cancel waitlisted user
            try:
                self.waitlist.remove(user_id)
                self.all_users.remove(user_id)
            except ValueError:
                raise NotFound(f"{user_id} not found")

    def status(self, user_id: str) -> UserStatus:

        if user_id in self.registered:
            return UserStatus("registered")

        if user_id in self.waitlist:
            position = list(self.waitlist).index(user_id) + 1
            return UserStatus("waitlisted", position)

        return UserStatus("none")

    def snapshot(self) -> dict:

        return {
            "capacity": self.capacity,
            "registered": list(self.registered),
            "waitlist": list(self.waitlist)
        }