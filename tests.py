import pytest

from solution import EventRegistration, UserStatus, DuplicateRequest, NotFound


def test_register_until_capacity_then_waitlist_fifo_positions():
    er = EventRegistration(capacity=2)

    s1 = er.register("u1")
    s2 = er.register("u2")
    s3 = er.register("u3")
    s4 = er.register("u4")

    assert s1 == UserStatus("registered")
    assert s2 == UserStatus("registered")
    assert s3 == UserStatus("waitlisted", 1)
    assert s4 == UserStatus("waitlisted", 2)

    snap = er.snapshot()
    assert snap["registered"] == ["u1", "u2"]
    assert snap["waitlist"] == ["u3", "u4"]


def test_cancel_registered_promotes_earliest_waitlisted_fifo():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist
    er.register("u3")  # waitlist

    er.cancel("u1")  # should promote u2

    assert er.status("u1") == UserStatus("none")
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u2"]
    assert snap["waitlist"] == ["u3"]


def test_duplicate_register_raises_for_registered_and_waitlisted():
    er = EventRegistration(capacity=1)
    er.register("u1")
    with pytest.raises(DuplicateRequest):
        er.register("u1")

    er.register("u2")  # waitlisted
    with pytest.raises(DuplicateRequest):
        er.register("u2")


def test_waitlisted_cancel_removes_and_updates_positions():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist pos1
    er.register("u3")  # waitlist pos2

    er.cancel("u2")    # remove from waitlist

    assert er.status("u2") == UserStatus("none")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["u3"]


def test_capacity_zero_all_waitlisted_and_promotion_never_happens():
    er = EventRegistration(capacity=0)
    assert er.register("u1") == UserStatus("waitlisted", 1)
    assert er.register("u2") == UserStatus("waitlisted", 2)

    # No one can ever be registered when capacity=0
    assert er.status("u1") == UserStatus("waitlisted", 1)
    assert er.status("u2") == UserStatus("waitlisted", 2)
    assert er.snapshot()["registered"] == []

    # Cancel unknown should raise NotFound
    with pytest.raises(NotFound):
        er.cancel("missing")



#################################################################################
# Add your own additional tests here to cover more cases and edge cases as needed.
#################################################################################

def test_ac1_single_registration_added_to_registered():
    # AC1: capacity 5, Alpha registers → registered list size becomes 1
    er = EventRegistration(capacity=5)

    status = er.register("Alpha")

    assert status == UserStatus("registered")

    snap = er.snapshot()
    assert snap["registered"] == ["Alpha"]
    assert snap["waitlist"] == []


def test_ac2_registration_goes_to_waitlist_when_capacity_full():
    # AC2: capacity full → new user added to waitlist
    er = EventRegistration(capacity=3)

    er.register("Alpha")
    er.register("Bravo")
    er.register("Charlie")

    status = er.register("Delta")

    assert status == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["Alpha", "Bravo", "Charlie"]
    assert snap["waitlist"] == ["Delta"]


def test_ac3_cancel_promotes_waitlisted_user():
    # AC3: cancel registered user promotes earliest waitlisted
    er = EventRegistration(capacity=2)

    er.register("Alpha")
    er.register("Bravo")
    er.register("Charlie")  # waitlisted

    er.cancel("Alpha")

    assert er.status("Charlie") == UserStatus("registered")

    snap = er.snapshot()
    assert snap["registered"] == ["Bravo", "Charlie"]
    assert snap["waitlist"] == []


def test_ac5_status_reports_correct_waitlist_position():
    # AC5: status returns correct waitlist position
    er = EventRegistration(capacity=1)

    er.register("Alpha")
    er.register("Bravo")
    er.register("Echo")

    status = er.status("Echo")

    assert status == UserStatus("waitlisted", 2)

def test_reregister_after_cancel_allowed():
    er = EventRegistration(capacity=1)

    er.register("Alpha")
    er.cancel("Alpha")

    status = er.register("Alpha")

    assert status == UserStatus("registered")

    snap = er.snapshot()
    assert snap["registered"] == ["Alpha"]
    assert snap["waitlist"] == []

def test_status_unknown_user_returns_none():
    er = EventRegistration(capacity=2)

    status = er.status("Ghost")

    assert status == UserStatus("none")

# -----------------------------
# Core Functionality Tests
# -----------------------------

def test_register_until_capacity():
    event = EventRegistration(capacity=2)

    event.register("alice")
    event.register("bob")

    snapshot = event.snapshot()

    assert snapshot["registered"] == ["alice", "bob"]
    assert snapshot["waitlist"] == []
    assert len(snapshot["registered"]) <= event.capacity


def test_waitlist_after_capacity_reached():
    event = EventRegistration(capacity=1)

    event.register("alice")
    status = event.register("bob")

    snapshot = event.snapshot()

    assert snapshot["registered"] == ["alice"]
    assert snapshot["waitlist"] == ["bob"]
    assert status.state == "waitlisted"
    assert status.position == 1


def test_fifo_waitlist_promotion():
    event = EventRegistration(capacity=1)

    event.register("alice")
    event.register("bob")
    event.register("carol")

    event.cancel("alice")

    snapshot = event.snapshot()

    assert snapshot["registered"] == ["bob"]
    assert snapshot["waitlist"] == ["carol"]


def test_prevent_duplicate_registration():
    event = EventRegistration(capacity=2)

    event.register("alice")

    with pytest.raises(DuplicateRequest):
        event.register("alice")


def test_status_queries():
    event = EventRegistration(capacity=1)

    event.register("alice")
    event.register("bob")

    assert event.status("alice").state == "registered"
    assert event.status("bob").state == "waitlisted"
    assert event.status("bob").position == 1
    assert event.status("unknown").state == "none"


# -----------------------------
# Edge Case Tests
# -----------------------------

def test_capacity_zero_all_waitlisted():
    """Edge Case: Capacity = 0"""
    event = EventRegistration(capacity=0)

    s1 = event.register("alice")
    s2 = event.register("bob")

    snapshot = event.snapshot()

    assert snapshot["registered"] == []
    assert snapshot["waitlist"] == ["alice", "bob"]
    assert s1.state == "waitlisted"
    assert s2.state == "waitlisted"


def test_waitlisted_user_cancels_before_promotion():
    """Edge Case: Waitlisted user cancels before promotion"""
    event = EventRegistration(capacity=1)

    event.register("alice")
    event.register("bob")
    event.register("carol")

    event.cancel("bob")

    snapshot = event.snapshot()

    assert snapshot["registered"] == ["alice"]
    assert snapshot["waitlist"] == ["carol"]


def test_multiple_cancellations_promote_in_order():
    """Edge Case: Multiple cancellations in sequence"""
    event = EventRegistration(capacity=2)

    event.register("alice")
    event.register("bob")
    event.register("carol")
    event.register("dave")

    event.cancel("alice")
    event.cancel("bob")

    snapshot = event.snapshot()

    assert snapshot["registered"] == ["carol", "dave"]
    assert snapshot["waitlist"] == []