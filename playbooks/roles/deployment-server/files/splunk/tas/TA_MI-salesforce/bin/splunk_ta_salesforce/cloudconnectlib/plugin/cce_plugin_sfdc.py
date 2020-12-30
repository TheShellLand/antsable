from future import standard_library
standard_library.install_aliases()
from builtins import str
import io
import csv
import re
import urllib.request, urllib.parse, urllib.error
from datetime import datetime

from cloudconnectlib.common import log
from cloudconnectlib.core.ext import regex_search
from cloudconnectlib.core.ext import splunk_xml
from cloudconnectlib.core.ext import std_output
from cloudconnectlib.core.plugin import cce_pipeline_plugin
from solnlib.modular_input.event import XMLEvent

logger = log.get_cc_logger()

_FAULT_STRING_REGEX = '\<faultstring\>(?P<faultstring>.*)\<\/faultstring\>'
_DEFAULT_ERROR = "Login Salesforce failed. Please check your network environment and credentials."
LOG_ID = 'Id'
LOG_EVENT_TYPE = 'EventType'
LOG_DATE = 'LogDate'
EVENTS_BATCH_SIZE = 50000
CREATED_DATE = 'CreatedDate'

@cce_pipeline_plugin
def quote(string):
    """Quote string through urllib.quote"""
    return urllib.parse.quote(string)


def _to_bool(bool_value):
    return str(bool_value).strip().lower() == 'true'


@cce_pipeline_plugin
def filter_records_before_date(is_greater_than, events, field, value):
    """Filter all events which the value of field is equal given value."""
    if not _to_bool(is_greater_than):
        return events
    return [event for event in events if event.get(field, '') != value]


def _timestamp_to_float(timestamp):
    if not timestamp:
        return None
    try:
        utc_time = datetime.strptime(timestamp[:-5], '%Y-%m-%dT%H:%M:%S.%f')
        return (utc_time - datetime(1970, 1, 1)).total_seconds()
    except Exception:
        logger.warning('Cannot convert timestamp %s to epoch time', timestamp)
        return None


@cce_pipeline_plugin
def log(level, log_message):
    """Print log with level, message should not contains %s"""
    logger.log(level, log_message)


@cce_pipeline_plugin
def convert_records_to_events(
        records,
        time_field,
        index=None,
        host=None,
        source=None,
        sourcetype=None,
        user_account_id=None):
    logger.debug(
        'Convert records to events time_field=%s, index=%s, host=%s, source=%s, sourcetype=%s, user_account_id=%s',
        time_field, index, host, source, sourcetype, user_account_id
    )

    # Adding user account id information in each record
    for record in records:
        record.update({'UserAccountId': user_account_id})

    return XMLEvent.format_events(
        XMLEvent(r,
                 time=_timestamp_to_float(r.get(time_field)),
                 index=index,
                 host=host,
                 source=source,
                 sourcetype=sourcetype) for r in records
    )


@cce_pipeline_plugin
def read_event_log_file(stream, log_file, index, host, source, sourcetype, user_account_id):

    # Condition to return when file does not exist in Salesforce environment
    if "NOT_FOUND" in stream:
        return

    if '\x00' in stream:
        logger.info("Removed NULL bytes encountered in event log file ID {}".format(log_file[LOG_ID]))
        fv = io.StringIO(stream.replace('\x00', ''))
    else:
        fv = io.StringIO(stream)

    csv_reader = csv.DictReader(fv)
    records = []
    log_id = log_file[LOG_ID]

    if not csv_reader:
        logger.info('No record found in csv file %s', log_id)
        return

    log_info = 'SFDCLogType="{}" SFDCLogId="{}" SFDCLogDate="{}"'.format(
        log_file[LOG_EVENT_TYPE], log_id, log_file[LOG_DATE]
    )

    total_records = 0
    for row in csv_reader:
        total_records += 1
        regex = '(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\.(\d+)'
        m = re.match(regex, row['TIMESTAMP'])
        event_time = '{}-{}-{}T{}:{}:{}.{}+0000'.format(
            m.group(1), m.group(2), m.group(3), m.group(4), m.group(5),
            m.group(6), m.group(7)
        )

        event = [event_time, log_info]
        event.extend('{}="{}"'.format(k, v) for k, v in row.items())
        # Appending user account id information to each eventlog
        event.append('UserAccountId="' + user_account_id + '"')
        records.append(' '.join(event))
        # Check if the batch size reached if yes then format records to event and index them
        if len(records) > EVENTS_BATCH_SIZE:
            xml_event = splunk_xml(records, '', index, host, source, sourcetype)
            std_output(xml_event)
            # Reset records object
            del records
            records = []
            logger.debug('Batch process collected %s events from csv file id=%s', str(total_records), log_id)
    # This code block is to index left over events which are not formatted/indexed when the batch size is less than 50k
    if len(records) > 0:
        xml_event = splunk_xml(records, '', index, host, source, sourcetype)
        std_output(xml_event)
        del records
    logger.info('Read %s events collected from csv file id=%s', str(total_records), log_id)
    fv.close()
    return


@cce_pipeline_plugin
def build_query(is_greater_than, object_name, object_fields, order_by, limit, start_date, sorting_order):
    soql = 'SELECT {} FROM {} WHERE {}'.format(object_fields, object_name, order_by)
    if _to_bool(is_greater_than):
        soql += '>{} ORDER BY {} {} LIMIT {}'.format(start_date, order_by, sorting_order ,limit)
    else:
        soql += '={}'.format(start_date)
    return soql


@cce_pipeline_plugin
def check_login_result(session_id, server_url, response):
    if response:
        logger.debug("Got login response from server with server_url: " + server_url)

    if session_id and server_url:
        return False

    if not session_id:
        logger.debug("Couldn't get session_id from response")
    if not server_url:
        logger.debug("Couldn't get server_url from response")

    error = regex_search(_FAULT_STRING_REGEX, response) if response else {}
    fault_string = error.get('faultstring', _DEFAULT_ERROR)
    logger.error(fault_string or _DEFAULT_ERROR)
    return True


@cce_pipeline_plugin
def exclude_fields(records, hourly):
    if not hourly:
        return [{k: r[k] for k in (LOG_ID, LOG_EVENT_TYPE, LOG_DATE)} for r in records]
    else:
        return [{k: r[k] for k in (LOG_ID, LOG_EVENT_TYPE, LOG_DATE, CREATED_DATE)} for r in records]

@cce_pipeline_plugin
def comparator_for(is_greater_than):
    logger.debug('is_greater_than=%s', is_greater_than)
    return ">=" if _to_bool(is_greater_than) or not is_greater_than else "="


@cce_pipeline_plugin
def filter_not_indexed_records(records, indexed_records):
    logger.debug('Filtering records not in %s', indexed_records)
    if not indexed_records:  # indexed records maybe a empty string
        logger.debug('No events are indexed. Return all the events.')
        return records
    return [r for r in records if r[LOG_ID] not in indexed_records]


@cce_pipeline_plugin
def refresh_start_date(comparator, previous_empty, start_date, next_start_date, new_start_date):
    logger.debug('comparator="%s" previous_empty=%s start_date=%s next_start_date=%s'
                 ' new_start_date=%s',
                 comparator, previous_empty, start_date, next_start_date, new_start_date)
    if comparator.strip() == '=':
        # Migrate from 1.0beta
        if not _to_bool(previous_empty):
            start_date = next_start_date
    elif new_start_date:
        # If no records returned, new_start_date is ""
        start_date = new_start_date
    logger.debug('Next round start_date=%s', start_date)
    return start_date


@cce_pipeline_plugin
def extract_ids_on_date(records, include_date, default_records, hourly):
    if not records:
        logger.info("No records returned, return original records %s", default_records)
        return default_records
    if not hourly:
        rv = [r[LOG_ID] for r in records if r[LOG_DATE] == include_date]
    else:
        rv = [r[LOG_ID] for r in records if r[CREATED_DATE] == include_date]
    logger.debug('include_date=%s, extracted ids=%s', include_date, rv)
    return rv


@cce_pipeline_plugin
def refresh_checkpoint(name, records, ckpt_mgr):
    # FIXME Remove indexed event log file from checkpoint.
    left_records = []
    if not records:
        logger.info("No records found in checkpoint, don't need to clean up checkpoint.")
        return left_records
    for record in records:
        log_id = record[LOG_ID]
        try:
            if ckpt_mgr.delete_if_exists([log_id]):
                logger.debug('Cleaned checkpoint for log id=%s', log_id)
            else:
                left_records.append(record)
        except Exception:
            logger.exception('Cannot delete checkpoint for log id=%s', log_id)

    num_left, num_total = len(left_records), len(records)
    logger.info('%s records found in checkpoint. %s files are not finished.', num_total, num_left)

    if num_left < num_total:
        logger.info(
            '%s file(s) are indexed successfully. Remove them from checkpoint.',
            num_total - num_left
        )
        namespaces = [name]
        checkpoint = ckpt_mgr.get_ckpt(namespaces)
        checkpoint['records'] = left_records
        ckpt_mgr.update_ckpt(ckpt=checkpoint, namespaces=namespaces)
        ckpt_mgr.close()
    return left_records
