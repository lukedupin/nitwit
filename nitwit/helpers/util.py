from django.conf import settings
from django.utils.timezone import utc
from python_http_client import BadRequestsError

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId

from twilio.rest import Client
from twilio.base.exceptions import TwilioException, TwilioRestException

from tzwhere import tzwhere

import datetime, math, re, pytz, base64, uuid, hashlib, os


def sendSms( body, to ):
    try:
        client = Client( settings.TWILIO_SMS['ACCOUNT_SID'],
                         settings.TWILIO_SMS['AUTH_TOKEN'] )

        message = client.messages.create(body=body, to=to,
                                         from_=settings.TWILIO_SMS['PHONE_NUMBER'])

    except TwilioException as e:
        print(e)
        return None

    except TwilioRestException as e:
        print(e)
        return None

    return message.sid


def sendEmail( to_email, subject, body, attachment=None ):
    # to_email could be a single string or a list of strings
    if isinstance(to_email, list):
        for email in to_email:
            if email.find('@') < 0:
                return None
    else:
        if to_email.find('@') < 0:
            return None

    message = Mail(
        from_email=settings.SEND_GRID['FROM_EMAIL'],
        to_emails=to_email,
        subject=subject,
        html_content=body)

    # Add an attachment?
    if attachment is not None:
        with open(attachment, "rb") as handle:
            encoded = base64.b64encode(handle.read()).decode()
            attach = Attachment()
            attach.file_content = FileContent(encoded)
            attach.file_type = FileType('application/csv')
            attach.file_name = FileName( attachment.split('/')[-1])
            attach.disposition = Disposition('attachment')
            attach.content_id = ContentId(str(uuid.uuid4()))
            message.attachment = attach

    response = None
    try:
        sg = SendGridAPIClient(settings.SEND_GRID['API_KEY'])
        response = sg.send(message)
        #print(response.status_code)
        #print(response.body)
        #print(response.headers)
    except KeyError as e:
        print("Invalid API key!")
        return None
    except BadRequestsError as e:
        print(f"Bad request for email: {to_email}")
        return None

    return response


def xlist( ary ):
    if ary is None:
        return []
    if isinstance(ary, str):
        return ','.split(ary)
    return list(ary)


def xtuple( tup ):
    return tuple(tup) if tup is not None else tuple()


def xstr( s, none='' ):
    return str(s) if s is not None else none


def xint( s, none=0, undefined=None ):
    try:
      if s == "undefined":
        return undefined
      return int(s) if s is not None and s != 'NaN' else none
    except ValueError:
        #Floating points and trailing letters wont fool me!!!
        m = re.search('^[-+]?[0-9]+', s)
        if m:
            return int(m.group(0))

        #can't go any further
        return none
    except TypeError:
        return none


def xfloat( s, none=0.0, undefined=None ):
    try:
        if s == "undefined":
            return undefined
        f = float(s) if s is not None and s != 'NaN' else none
        if math.isnan(f):
            return none
        return f
    except ValueError:
        #trailing letters wont fool me!!!
        m = re.search('^[-+]?[0-9]*\.?[0-9]+', s )
        if m:
            return float(m.group(0))

        #Can't go any further
        return none
    except TypeError:
        return none


def xbool( s, none=False, undefined=False ):
    #Are we string? try to figure out what that means
    if isinstance( s, str ):
        s = s.lower()
        if s == 'true':
            return True
        elif s == 'none' or s == 'null':
            return none
        elif s == 'undefined':
            return undefined
        else:
            return False

    #Special case none
    elif s is None:
        return none
    else:
        return bool(s)


def xlen( x, none=0 ):
    return len(x) if x is not None else none


def cap( value, largest, smallest=0 ):
    if isinstance( value, int ) or isinstance( value, float ):
        value = round( value )
    return max( min( xint( value ), largest ), smallest )


def upperCaseFirst( s ):
    return ' '.join([x.capitalize() for x in s.split(' ')])


def snakeToCamel( s ):
    return ''.join( [x.capitalize() for x in xstr(s).split('_')])


def camelToSnake( s ):
    s = xstr(s)
    return (s[0] + re.sub('([A-Z])', r'_\1', s[1:])).lower()


# Cap a value between the given bounds
def cap( val, high, low=None ):
    if not low:
        low = -high
    if val > high:
        val = high
    elif val < low:
        val = low

    return val


# Careful, this is SUPER SLOW
def calculateTimezone( lat, lng ):
    return tzwhere.tzwhere().tzNameAt( lat, lng )


# Provide a timezone
def toTimezone( tz=None ):
    timezone = utc
    if tz is not None:
        try:
            timezone = pytz.timezone(str(tz))
        except pytz.UnknownTimeZoneError:
            pass

    return timezone


# Return the hour differnce between two timezones
def tzToTz( to_tz, from_tz=None ): # None means UTC
    return round((unixNow(None, to_tz) - unixNow(None, from_tz)) / 3600000) # Hours


# Get the current time
def timeNow( ms=None, tz=None ):
    # Give the user their info
    ts = datetime.datetime.now( toTimezone(tz) )
    if ms:
        return ts + datetime.timedelta(milliseconds=xint(ms))
    else:
        return ts


# Get a time prior to any possible question
def timeBeginning():
    return datetime.datetime(2021, 1, 1, tzinfo=utc)


# Convert a time to different timezone
def timeToTz( ts, tz ):
    return ts + datetime.timedelta(hours=tzToTz( tz )) - datetime.timedelta(hours=tzToTz("UTC", ts.tzinfo))


# Convert a time into epoch format
def timeToUnix( ts ):
    return int(ts.timestamp() * 1000.0) if ts else 0


# Get current days since epoc
def timeToDays( ts=None ):
    if ts is None:
        ts = timeNow()
    return (ts - datetime.datetime(1970, 1, 1, tzinfo=ts.tzinfo)).days


def timeToWeek( offset, now=None ):
    if now is None:
        now = timeNow()

    days = offset * 7 - now.weekday()
    return datetime.datetime(year=now.year, month=now.month, day=now.day, tzinfo=now.tzinfo) + \
           datetime.timedelta(days=days)


def timeToMonth( offset, now=None ):
    if now is None:
        now = timeNow()

    year = now.year
    month = now.month + xint(offset)
    while month > 12:
        year += 1
        month -= 12

    while month < 1:
        year -= 1
        month += 12

    return datetime.datetime(year=year, month=month, day=1, tzinfo=now.tzinfo)


def timeToQuarter( quarter, now=None ):
    if now is None:
        now = timeNow()

    offset = 0
    while ((now.month + offset) - 1) % 3 != 0:
        offset -= 1

    return timeToMonth( offset + xint(quarter) * 3, now )


def timeToYear( year, now=None ):
    if now is None:
        now = timeNow()

    return timeToMonth( 1 - now.month + xint(year) * 12, now )


def daysToTime( days ):
    return datetime.datetime(1970, 1, 1, tzinfo=utc) + datetime.timedelta(days=days)


def unixToDays( unix=None ):
    if unix is None:
        unix = unixNow()
    return math.floor(unix / 86400000)


def daysToUnix( days ):
    return days * 86400000


# convert date to string readable
def dateToStr( date ):
    if date is None:
        return "0-0-0"
    return "%d-%d-%d" % (date.month, date.day, date.year)


# Current time in epoch format
def unixNow( ms=None, tz=None ):
    return timeToUnix( timeNow( ms, tz ) )


# Convert a time to different timezone
def unixToTz( unix, tz, from_tz="UTC" ):
    return unix + (tzToTz( tz ) - tzToTz("UTC", from_tz)) * 3600000


# Convert an epoch format into time
def unixToTime( ms, tz=None ):
    timezone = toTimezone(tz)
    return datetime.datetime.fromtimestamp( xfloat(ms) / 1000.0 ).replace(tzinfo=timezone)


# Check if a timestamp is in range
def timeInRange( ts, ms_range, center_ts=None ):
    if ts is None:
        return False

    return unixInRange( timeToUnix(ts), ms_range, center_ts )


# True if one date is within range of another
def unixInRange( unix_ts, ms_range, center_ts=None ):
    unix_ts = xint( unix_ts )
    if center_ts is None:
        center_ts = unixNow()

    return unix_ts < center_ts + ms_range and unix_ts > center_ts - ms_range


def deltaToSeconds( d, digits=None ):
    ts = d.days * 86400000.0 + float(d.seconds) + float(d.microseconds / 1000.0)
    if digits:
        return round( math.fabs( ts ), digits )
    else:
        return math.fabs( ts )


# Day of year to date
def doyToDate( doy ):
    return datetime.datetime( int(doy / 400) + 2000, 1, 1 ) + datetime.timedelta( (doy % 400) - 1 )


def humanDate( date=None, add_sec=0, force_hours=False, force_full=False ):
    if date is None:
        date = timeNow()

    if isinstance( date, datetime.datetime ):
        return date.strftime( "%m/%d/%Y %I:%M:%S%p" )
    elif isinstance( date, datetime.timedelta ):
        date = int( deltaToSeconds( date ))

    # Return the delta
    date = int(date) + add_sec
    if date >= 3600 or force_full:
        return "%d:%02d:%02d" % (int(date / 3600), int((date / 60) % 60), int(date % 60))
    elif date >= 60:
        if force_hours:
            return "00:%02d:%02d" % (int((date / 60) % 60), int(date % 60))
        else:
            return "%d:%02d" % (int((date / 60) % 60), int(date % 60))
    elif date > 1:
        return "%d seconds" % int(date % 60)
    elif date == 1:
        return "%d second" % int(date % 60)
    else:
        return '0'


def weekOfMonth( ts ):
    dow = ts.weekday()

    tmp = datetime.datetime(year=ts.year, month=ts.month, day=1)
    while tmp.weekday() != dow:
        tmp += datetime.timedelta(days=1)

    if ts.day < tmp.day:
        print("How the fuck")
        return None

    week = 0
    while ts.day > tmp.day:
        week += 1
        tmp += datetime.timedelta(days=7)

    return week


# Generate reset code
def hash_code():
    # Create the reset code
    m = hashlib.sha256()
    m.update(b"A super important message that must happen")
    m.update(bytes(str(unixNow()), 'utf-8'))
    m.update(bytes(str(uuid.uuid4()), 'utf-8'))

    # Save the pwd reset code
    return m.hexdigest()


def is_eof(handle):
    return handle.tell() == os.fstat(handle.fileno()).st_size


def sha256sum(filename):
    if not os.path.exists(filename):
        return None

    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()