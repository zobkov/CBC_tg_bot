"""
ICS file generator for online lectures
Generates .ics (iCalendar) files for adding events to calendar applications
"""

import logging
from pathlib import Path
from datetime import timedelta

from icalendar import Calendar, Event, Alarm

from app.infrastructure.database.models.online_events import OnlineEventModel
from app.utils.datetime_formatters import MOSCOW_TZ


logger = logging.getLogger(__name__)


def generate_ics_file(event: OnlineEventModel, output_path: Path) -> Path:
    """
    Generate an ICS file for an online lecture event
    
    Args:
        event: OnlineEventModel instance with lecture details
        output_path: Path object pointing to the output file location
    
    Returns:
        Path to the generated ICS file
    
    Raises:
        OSError: If file cannot be written
    """
    # Create calendar object
    cal = Calendar()
    cal.add('prodid', '-//CBC Crew Selection Bot//Online Lectures//RU')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    
    # Create event
    ics_event = Event()
    
    # Add event properties
    ics_event.add('summary', event.title)
    ics_event.add('dtstart', event.start_at)
    ics_event.add('dtend', event.end_at)
    
    # Generate unique ID for the event
    ics_event.add('uid', f'{event.slug}@cbc-bot')
    
    # Build description
    description_parts = []
    if event.speaker:
        description_parts.append(f"Спикеры: {event.speaker}.")
    
    if event.description:
        # Remove all newlines and replace with spaces as per spec
        clean_description = event.description.replace('\n', ' ').replace('\r', ' ')
        # Remove multiple spaces
        clean_description = ' '.join(clean_description.split())
        description_parts.append(f"Описание: {clean_description}")
    
    if description_parts:
        ics_event.add('description', ' '.join(description_parts))
    
    # Add location (URL)
    if event.url:
        ics_event.add('location', event.url)
    
    # Add timestamp
    from datetime import datetime
    ics_event.add('dtstamp', datetime.now(MOSCOW_TZ))
    
    # Add reminder (VALARM) - 15 minutes before
    # Use short description to avoid line breaking issues on iOS
    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('description', 'Напоминание о лекции')
    alarm.add('trigger', timedelta(minutes=-15))
    
    # Add alarm to event
    ics_event.add_component(alarm)
    
    # Add event to calendar
    cal.add_component(ics_event)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to file
    try:
        # Generate ICS content
        ics_content = cal.to_ical()
        
        # Fix RFC 5545 line folding issues:
        # The icalendar library sometimes adds double spaces after line breaks
        # which causes iOS Calendar to reject the file
        # RFC 5545 requires exactly ONE space after CRLF for continuation
        
        # Decode to string, fix double spaces, encode back
        ics_str = ics_content.decode('utf-8')
        
        # Replace any occurrence of \r\n followed by 2+ spaces with \r\n and single space
        import re
        ics_str = re.sub(r'\r\n {2,}', r'\r\n ', ics_str)
        
        # Write corrected content
        with open(output_path, 'wb') as f:
            f.write(ics_str.encode('utf-8'))
        
        logger.info(f"Generated ICS file for event '{event.slug}' at {output_path}")
        return output_path
    
    except OSError as e:
        logger.error(f"Failed to write ICS file for '{event.slug}': {e}")
        raise
