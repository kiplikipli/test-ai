from models.meeting_state import MeetingState


CONFIRM_WORDS = {'yes', 'confirm', 'approved', 'go ahead', 'book it'}


def is_explicit_confirmation(message: str) -> bool:
    lowered = message.lower()
    return any(token in lowered for token in CONFIRM_WORDS)


def can_create_meeting(state: MeetingState) -> bool:
    return bool(state.selected_slot and state.attendees)
