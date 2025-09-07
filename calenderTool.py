import datetime as dt
import os.path
from langchain_core.tools import tool
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import random
import pytz
from dateutil.parser import parse # Helps parse "2 PM tomorrow"
import streamlit as st

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():
    """
    Builds and returns an authorized Google Calendar service object.
    Checks st.session_state for credentials.
    Returns None if credentials are not available.
    """
    if 'credentials' not in st.session_state or not st.session_state['credentials']:
        st.error("Authentication required. Please log in to connect to Google Calendar.")
        raise Exception("No credentials in session state.")
    
    try:
        # Build the service object from the credentials in session state
        service = build('calendar', 'v3', credentials=st.session_state['credentials'])
        return service
    except Exception as e:
        st.error(f"Failed to create Google Calendar service: {e}")
        raise

@tool
def get_events_between_start_and_end(start_time, end_time):
    '''Fetches calendar events within a specified time range.

    Args:
        start_time (str): The start time for the event search (in this YYYY-MM-DDTHH:MM:SS format).
        end_time (str): The end time for the event search (in this YYYY-MM-DDTHH:MM:SS format).

    Returns:
        str: A string representation of a list of dictionaries, where each dictionary contains the start time, end time, and summary of an event.
    '''
    service = get_calendar_service()
    try:
        
        calendar_info = service.calendars().get(calendarId='primary').execute()
        timezone_str = calendar_info['timeZone']
        user_timezone = pytz.timezone(timezone_str)
        st = parse(start_time)
        local_datetime = user_timezone.localize(st)
        start_time = local_datetime.isoformat()
        et = parse(end_time)
        local_datetime = user_timezone.localize(et)
        end_time = local_datetime.isoformat()
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return
    # Prints the start and name of the next 10 events
        result = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            result.append({'start_time': start, 'end_time': end, 'summary': event["summary"]})
        result = str(result)
        return result

    except HttpError as error:
        print(f"An error occurred: {error}")
        return error
@tool
def set_calender_event(start_time, end_time, summary = None, location = None, description = None, recurrence=None, attendees=[]):
    '''Creates a new event in the calendar.

    Args:
        start_time (str): The start time of the event (in this YYYY-MM-DDTHH:MM:SS format).
        end_time (str): The end time of the event (in this YYYY-MM-DDTHH:MM:SS format).
        summary (str, optional): The summary or title of the event.
        location (str, optional): The location of the event.
        description (str, optional): A description of the event.
        recurrence (list, optional): A list of recurrence rules for the event. Defaults to None.
        attendees (list, optional): A list of dictionaries, each containing the email of an attendee. Defaults to [].

    Returns:
        None: The function prints the HTML link of the created event or an error message.
    '''
    service = get_calendar_service()
    try:
        calendar_info = service.calendars().get(calendarId='primary').execute()
        timezone_str = calendar_info['timeZone']
        user_timezone = pytz.timezone(timezone_str)
        st = parse(start_time)
        local_datetime = user_timezone.localize(st)
        start_time = local_datetime.isoformat()
        et = parse(end_time)
        local_datetime = user_timezone.localize(et)
        end_time = local_datetime.isoformat()
        # user_timezone = pytz.timezone(timezone_str)

        color = random.randint(1, 11)

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'colorId': color,
            'start': {
                'dateTime': start_time,
                'timeZone': timezone_str,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': timezone_str,
            },
            'recurrence': recurrence,
            'attendees': attendees
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")

    except HttpError as error:
        print(f"An error occurred in creating the event: {error}")
        return error
    
@tool
def find_event_by_name(
    event_name: str, 
):
    """
    Finds a specific event by name in the Google Calendar.

    Args:
        event_name (str): The name of the event to find.

    Returns:
        list[str]: A list of up to 5 suggested available time slots in ISO format.
                   Returns an error string if the event is not found.
    """
    try:
        # service = login_calender()
        service = get_calendar_service()

        # Get the calendar's timezone
        calendar_info = service.calendars().get(calendarId='primary').execute()
        timezone_str = calendar_info['timeZone']
        user_timezone = pytz.timezone(timezone_str)

        # 1. Find the anchor event
        now = dt.datetime.now(user_timezone)
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=now.isoformat(),
            q=event_name, # Search for the event by name
            maxResults=1, 
            singleEvents=True, 
            orderBy='startTime'
        ).execute()
        
        anchor_event = events_result.get('items', [])
        if not anchor_event:
            return f"Error: Event '{event_name}' not found in your upcoming calendar."
        return f"found event {anchor_event}"
        # Get the end time of the anchor event and parse it
        # end_time_str = anchor_event[0]['end'].get('dateTime', anchor_event[0]['end'].get('date'))
        # anchor_event_end = dt.datetime.fromisoformat(end_time_str)
    except Exception as e:
        return f"Error during authentication or fetching events: {e}"

@tool
def get_current_date_time():
    """Returns the current date and time in ISO format. Helps to reference what amboiguous times(like 'tomorrow' , 'today' etc) mean."""
    service = get_calendar_service()
    calendar_info = service.calendars().get(calendarId='primary').execute()
    timezone_str = calendar_info['timeZone']
    user_timezone = pytz.timezone(timezone_str)
    print(f"Calendar timezone: {type(user_timezone)}")
    return dt.datetime.now(user_timezone).isoformat()

# @tool
# def get_free_availability(start_time: str, end_time: str):
#     """
#     Finds free time slots in the calendar within a given time range, assuming work hours are 9 AM to 5 PM.

#     Args:
#         start_time (str): The start of the date range to check for availability (e.g., 'today', 'tomorrow', '2025-09-10').
#         end_time (str): The end of the date range to check for availability (e.g., 'today', 'tomorrow', '2025-09-10').

#     Returns:
#         str: A string listing available 1-hour slots or a message indicating no availability.
#     """
#     service = get_calendar_service()
#     try:
#         calendar_info = service.calendars().get(calendarId='primary').execute()
#         timezone_str = calendar_info['timeZone']
#         user_timezone = pytz.timezone(timezone_str)

#         # Parse start and end times and set them to the working hours for those days
#         start_dt = parse(start_time).astimezone(user_timezone).replace(hour=9, minute=0, second=0, microsecond=0)
#         end_dt = parse(end_time).astimezone(user_timezone).replace(hour=17, minute=0, second=0, microsecond=0)

#         body = {
#             "timeMin": start_dt.isoformat(),
#             "timeMax": end_dt.isoformat(),
#             "timeZone": timezone_str,
#             "items": [{"id": "primary"}]
#         }

#         free_busy_result = service.freebusy().query(body=body).execute()
#         busy_slots = free_busy_result.get('calendars', {}).get('primary', {}).get('busy', [])

#         if not busy_slots:
#             return f"The entire time from {start_dt.strftime('%I:%M %p')} to {end_dt.strftime('%I:%M %p')} is free."

#         # Generate potential 1-hour slots and check against busy slots
#         available_slots = []
#         current_time = start_dt
#         while current_time < end_dt:
#             slot_end = current_time + dt.timedelta(hours=1)
#             is_free = True
#             for busy in busy_slots:
#                 busy_start = parse(busy['start'])
#                 busy_end = parse(busy['end'])
#                 # Check for overlap
#                 if max(current_time, busy_start) < min(slot_end, busy_end):
#                     is_free = False
#                     break
            
#             if is_free:
#                 available_slots.append(current_time.strftime('%Y-%m-%d %I:%M %p'))
            
#             current_time += dt.timedelta(minutes=30) # Check every half hour for a new potential slot

#         if not available_slots:
#             return "No 1-hour slots are available in the specified range."
        
#         return "The following 1-hour slots are available: " + ", ".join(list(set(available_slots)))

#     except Exception as e:
#         return f"An error occurred while checking availability: {e}"


def _find_event_id(service, event_name_query: str):
    """Internal helper function to find an event's ID by its name."""
    now = dt.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        q=event_name_query,
        timeMin=now,
        maxResults=1,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    if not events:
        return None
    return events[0]['id']

@tool
def update_event(event_name: str, new_summary: str = None, new_start_time: str = None, new_end_time: str = None, new_location: str = None):
    """
    Updates an existing event in the calendar. You must provide the original name and at least one new detail to change.

    Args:
        event_name (str): The name/summary of the event to find and update.
        new_summary (str, optional): The new name or summary for the event.
        new_start_time (str, optional): The new start time for the event (e.g., '2025-09-10T14:00:00').
        new_end_time (str, optional): The new end time for the event (e.g., '2025-09-10T15:00:00').
        new_location (str, optional): The new location for the event.

    Returns:
        str: A confirmation message with the link to the updated event or an error message.
    """
    service = get_calendar_service()
    try:
        event_id = _find_event_id(service, event_name)
        if not event_id:
            return f"Error: Could not find an upcoming event named '{event_name}'."

        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # Update fields if new values are provided
        if new_summary:
            event['summary'] = new_summary
        if new_location:
            event['location'] = new_location
        if new_start_time:
            event['start']['dateTime'] = parse(new_start_time).isoformat()
        if new_end_time:
            event['end']['dateTime'] = parse(new_end_time).isoformat()
            
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return f"Event '{event_name}' updated successfully: {updated_event.get('htmlLink')}"
    except Exception as e:
        return f"An error occurred while updating the event: {e}"

@tool
def delete_event(event_name: str):
    """
    Deletes an event from the calendar by its name.

    Args:
        event_name (str): The name/summary of the event to delete.

    Returns:
        str: A confirmation that the event was deleted or an error message.
    """
    service = get_calendar_service()
    try:
        event_id = _find_event_id(service, event_name)
        if not event_id:
            return f"Error: Could not find an upcoming event named '{event_name}'."

        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return f"Event '{event_name}' was successfully deleted."
    except Exception as e:
        return f"An error occurred while deleting the event: {e}"



if __name__ == "__main__":
    print("Testing the calendar tools...")
    