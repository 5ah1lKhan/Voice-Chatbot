import datetime as dt
import os.path
from langchain_core.tools import tool
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import random
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


# # def main():
# def login_calender():
#     '''Tool to login in to calender'''
#     creds = None
#     try:
#         if os.path.exists("token.json"):
#             creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
#         if not creds or not creds.valid:
#             if creds and creds.expired and creds.refresh_token:
#                 creds.refresh(Request())
#             else:
#                 flow = InstalledAppFlow.from_client_secrets_file(
#                     "Calender_desktop_credentials.json", SCOPES
#                 )
#                 creds = flow.run_local_server(port=0)
            
#             with open("token.json", "w") as token:
#                 token.write(creds.to_json())
#         service = build("calendar", "v3", credentials=creds)
#         return service
#     except Exception as e:
#         print(f"Error during authentication: {e}")
#         raise

# @tool
# def get_next_n_events(n=10):
#     '''Tool to get the get next n events from calender'''
#     service = login_calender()
#     try:
        

#         # Call the Calendar API
#         # now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
#         now = dt.datetime.now().isoformat() + 'Z'
#         print("Getting the upcoming 10 events")
#         events_result = (
#             service.events()
#             .list(
#                 calendarId="primary",
#                 timeMin=now,
#                 maxResults=10,
#                 singleEvents=True,
#                 orderBy="startTime",
#             )
#             .execute()
#         )
#         events = events_result.get("items", [])

#         if not events:
#             print("No upcoming events found.")
#             return
#     # Prints the start and name of the next 10 events
#         result = []
#         for event in events:
#             start = event["start"].get("dateTime", event["start"].get("date"))
#             end = event["end"].get("dateTime", event["end"].get("date"))
#             result.append({'start_time': start, 'end_time': end, 'summary': event["summary"]})
#         result = str(result)
#         return result

#     except HttpError as error:
#         print(f"An error occurred: {error}")
#         return error

# @tool   
# def set_calender_event(summary, location, description, start_time, end_time, timezone='Asia/Kolkata', recurrence=None, attendees=[]):
#     '''Tool to set an event in the calendar'''
#     service = login_calender()
#     try:
#         color = random.randint(1, 11)

#         event = {
#             'summary': summary,
#             'location': location,
#             'description': description,
#             'colorId': color,
#             'start': {
#                 'dateTime': start_time,
#                 'timeZone': timezone,
#             },
#             'end': {
#                 'dateTime': end_time,
#                 'timeZone': timezone,
#             },
#             'recurrence': recurrence,
#             'attendees': attendees
#         }

#         event = service.events().insert(calendarId='primary', body=event).execute()
#         print(f"Event created: {event.get('htmlLink')}")

#     except HttpError as error:
#         print(f"An error occurred in creating the event: {error}")
#         return error


def login_calender():
    '''Tool to login in to calender'''
    creds = None
    try:
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "Calender_desktop_credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(creds.to_json())
        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        print(f"Error during authentication: {e}")
        raise
@tool
def get_events_between_start_and_end(start_time, end_time):
    '''Fetches calendar events within a specified time range.

    Args:
        start_time (str): The start time for the event search (in this YYYY-MM-DDTHH:MM:SSZ format).
        end_time (str): The end time for the event search (in this YYYY-MM-DDTHH:MM:SSZ format).

    Returns:
        str: A string representation of a list of dictionaries, where each dictionary contains the start time, end time, and summary of an event.
    '''
    service = login_calender()
    try:


        # Call the Calendar API
        # now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        now = dt.datetime.now().isoformat() + 'Z'
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
def set_calender_event(start_time, end_time, summary = None, location = None, description = None, timezone='Asia/Kolkata', recurrence=None, attendees=[]):
    '''Creates a new event in the calendar.

    Args:
        start_time (str): The start time of the event (in this YYYY-MM-DDTHH:MM:SSZ format).
        end_time (str): The end time of the event (in this YYYY-MM-DDTHH:MM:SSZ format).
        summary (str, optional): The summary or title of the event.
        location (str, optional): The location of the event.
        description (str, optional): A description of the event.
        timezone (str, optional): The timezone for the event. Defaults to 'Asia/Kolkata'.
        recurrence (list, optional): A list of recurrence rules for the event. Defaults to None.
        attendees (list, optional): A list of dictionaries, each containing the email of an attendee. Defaults to [].

    Returns:
        None: The function prints the HTML link of the created event or an error message.
    '''
    service = login_calender()
    try:
        color = random.randint(1, 11)

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'colorId': color,
            'start': {
                'dateTime': start_time,
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': timezone,
            },
            'recurrence': recurrence,
            'attendees': attendees
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")

    except HttpError as error:
        print(f"An error occurred in creating the event: {error}")
        return error


if __name__ == "__main__":
    print("Testing the calendar tools...")
    # get_next_n_events(10)
    # set_calender_event(
    #     summary="Meeting with team",
    #     location="Zoom",
    #     description="Discuss project updates",
    #     start_time="2025-09-13T10:00:00",
    #     end_time="2025-09-13T11:00:00",
    #     attendees=[
    #         {'email': 'sahilk.workks@example.com'},
    #         {'email': 'attendee2@example.com'}
    #     ]
    # )