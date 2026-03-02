import json
import logging

from agents.confirmation import can_create_meeting, is_explicit_confirmation
from agents.intent_parser import ParsedIntent, parse_intent
from models.attendee import Attendee
from models.date_range import DateRange
from models.meeting_state import MeetingState
from services.tool_client import ToolClientError, call_tool

logger = logging.getLogger(__name__)


async def process_message(state: MeetingState, message: str) -> tuple[MeetingState, str]:
    state_before = state.model_dump(mode='json')
    parsed = await parse_intent(message)

    _apply_parsed_updates(state, parsed)

    reply = await _decide_next_action(state, parsed, message)

    logger.info(
        json.dumps(
            {
                'session_id': state.session_id,
                'user_message': message,
                'parsed_intent': parsed.model_dump(mode='json'),
                'state_before': state_before,
                'state_after': state.model_dump(mode='json'),
            }
        )
    )
    return state, reply


def _apply_parsed_updates(state: MeetingState, parsed: ParsedIntent) -> None:
    if parsed.title:
        state.title = parsed.title
    if parsed.duration_minutes:
        state.duration_minutes = parsed.duration_minutes
    if parsed.attendee_names:
        state.attendees = [Attendee(name=name, priority='required') for name in parsed.attendee_names]
        state.status = 'resolving_attendees'
    if parsed.date_start and parsed.date_end and parsed.timezone:
        state.date_range = DateRange(start_date=parsed.date_start, end_date=parsed.date_end, timezone=parsed.timezone)
        if state.status in {'collecting', 'resolving_attendees'}:
            state.status = 'scheduling'


async def _decide_next_action(state: MeetingState, parsed: ParsedIntent, message: str) -> str:
    if state.status == 'resolving_attendees' and state.attendees:
        return await _resolve_attendees(state)

    if state.status == 'scheduling' and state.date_range and state.attendees:
        return await _schedule(state)

    if state.status == 'awaiting_confirmation':
        if (parsed.confirmation or is_explicit_confirmation(message)) and can_create_meeting(state):
            return await _create_meeting(state)
        if parsed.intent == 'modify':
            state.status = 'scheduling'
            return 'Understood. I will recompute availability with your updates.'
        return 'Please confirm to create the meeting, or tell me what you want to change.'

    missing = []
    if not state.title:
        missing.append('meeting title')
    if not state.attendees:
        missing.append('attendees')
    if not state.date_range:
        missing.append('date range')
    return f"Please provide the following: {', '.join(missing)}."


async def _resolve_attendees(state: MeetingState) -> str:
    payload = {
        'legal_entity_id': state.legal_entity_id,
        'requester_email': state.requester_email,
        'attendees': [a.model_dump(mode='json') for a in state.attendees],
    }
    try:
        result = await call_tool('tool/validate_employees', payload)
    except ToolClientError:
        return 'I could not validate attendees right now. Please retry in a moment.'

    invalid = result.get('invalid', [])
    valid = result.get('valid', [])
    state.attendees = [Attendee.model_validate(item) for item in valid]
    if invalid:
        return f"I could not validate: {', '.join(i.get('name', 'unknown') for i in invalid)}. Please adjust attendees."

    state.status = 'scheduling'
    return 'Attendees validated. I will now find optimal slots.'


async def _schedule(state: MeetingState) -> str:
    payload = {
        'legal_entity_id': state.legal_entity_id,
        'duration_minutes': state.duration_minutes,
        'attendees': [a.model_dump(mode='json') for a in state.attendees],
        'date_range': state.date_range.model_dump(mode='json') if state.date_range else None,
    }
    try:
        result = await call_tool('tool/find_optimal_availability', payload)
    except ToolClientError:
        return 'Scheduling service is temporarily unavailable. Please retry shortly.'

    slots = result.get('slots', [])
    if not slots:
        return 'No slots found in that range. Please expand your date range.'

    state.suggested_slots = slots[:5]
    state.selected_slot = state.suggested_slots[0]
    state.status = 'awaiting_confirmation'
    return 'Top options found. I selected the best slot. Reply “confirm” to book it, or ask for changes.'


async def _create_meeting(state: MeetingState) -> str:
    payload = {
        'legal_entity_id': state.legal_entity_id,
        'title': state.title,
        'requester_email': state.requester_email,
        'attendees': [a.model_dump(mode='json') for a in state.attendees],
        'selected_slot': state.selected_slot,
        'duration_minutes': state.duration_minutes,
    }
    try:
        result = await call_tool('tool/create_meeting', payload)
    except ToolClientError:
        return 'Meeting creation failed due to a temporary error. Please confirm again in a moment.'

    state.status = 'completed'
    return f"Meeting created successfully. Event ID: {result.get('eventId')} Link: {result.get('link')}"
