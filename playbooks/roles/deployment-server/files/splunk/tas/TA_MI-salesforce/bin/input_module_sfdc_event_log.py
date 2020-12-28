# encoding = utf-8
import import_declare_test

import logging

import sfdc_common as common
from cloudconnectlib.core.task import CCESplitTask, CCEHTTPRequestTask
from splunktaucclib.rest_handler import util
from splunk import rest
from cloudconnectlib.splunktacollectorlib.data_collection.ta_checkpoint_manager import TACheckPointMgr

from cloudconnectlib.core.plugin import cce_pipeline_plugin

util.remove_http_proxy_env_vars()

_DEFAULT_START_DATE = 30
_DEFAULT_LIMIT = 1000
_OAUTHFLOW = "oauth"


def validate_input(helper, definition):
    pass


def _index_event_log_file(task_config, meta_config):
    header = {
        'Authorization': 'Bearer {{session_id}}',
        'Accept-encoding': 'gzip',
        'X-PrettyPrint': '1'
    }
    request = {
        'url': '{{server_url}}/services/data/{{API_VERSION}}/sobjects'
               '/EventLogFile/{{event_log_file.Id}}/LogFile',
        'method': 'GET',
        'headers': header,
    }
    task = CCEHTTPRequestTask(request, 'EventLogFile', meta_config, task_config)
    task.set_iteration_count(1)
    task.configure_checkpoint(
        name='{{event_log_file.Id}}',
        content={
            'finished': True
        }
    )
    process_params = (
        ('set_var', ['sfdc_event_log://EventLog_{{account_name}}_{{input_name}}'], 'source'),
        ('read_event_log_file',
         ['{{__response__.body}}', '{{event_log_file}}', '{{index}}', '{{host}}', '{{source}}', '{{sourcetype}}',
          '{{user_account_id}}'],
         'records'),
    )
    # Get account name to append in source
    task.add_preprocess_handler('set_var', [task_config.get("account").get("name")], 'account_name')
    # Get input name to append in source
    task.add_preprocess_handler('set_var', [task_config.get("stanza_name")], 'input_name')
    task.add_postprocess_handler_batch(process_params)
    return task


def _build_query(task_config, logger):
    """Filter event log by Interval to avoid duplication"""
    interval = (task_config.get('monitoring_interval') or '').strip()

    lv = interval.lower()

    if lv == 'hourly':
        terms = ['SELECT Id,EventType,LogDate,CreatedDate FROM EventLogFile WHERE'
             ' CreatedDate{{comparator}}{{start_date}}']
        logger.info("Add-on will only collect event logs which interval is '%s'", interval)
        terms.append("AND Interval='%s'" % lv.capitalize())
        terms.append('ORDER BY CreatedDate LIMIT {{limit}}')
    else:
        terms = ['SELECT Id,EventType,LogDate FROM EventLogFile WHERE'
                 ' LogDate{{comparator}}{{start_date}}']
        if lv == 'daily':
            logger.info("Add-on will only collect event logs with an interval of '%s'", interval)
            terms.append("AND Interval='%s'" % lv.capitalize())
        terms.append('ORDER BY LogDate LIMIT {{limit}}')

    return ' '.join(terms)

def add_process_pipeline(task, task_config, meta_config, logger, helper_proxy, is_retry):

    soql = _build_query(task_config, logger)

     # For hourly log data collection, calculate necessary variables
    interval = (task_config.get('monitoring_interval') or '').strip()
    lv = interval.lower()
    hourly = True if lv == 'hourly' else False
    collection_date = "CreatedDate" if hourly is True else "LogDate"


    pre_params = (
        ('set_var', [False], 'is_token_refreshed'),
        ('exit_job_if_true', ['{{records_empty}}'], ''),
        ('exit_if_true', ['{{records_not_empty}}'], ''),

        # Reset checkpoint, records is loaded from checkpoint
        ('refresh_checkpoint', ['{{name}}', '{{records}}', task._checkpointer], 'records'),
        # Consume the records left in checkpoint
        ('exit_if_true', ['{{records|count>0}}'], ''),

        # Prepare query
        ('comparator_for', ['{{is_greater_than}}'], 'comparator'),
        ('set_var', [soql], 'query'),
        ('log', [logging.INFO, 'Query event logs soql={{query}}'], ''),
        ('quote', ['{{query}}'], 'query_string'),
        # Set the start_date_config to input stanza's Query Start Date to update in checkpoint
        ('set_var', [task_config.get('start_date_config')], 'start_date_config')
    )
    task.add_preprocess_handler_batch(pre_params)
    # In Case of oAuthflow check for authorization error and refresh the access token if required
    if not is_retry and task_config.get("account").get("auth_type") and task_config.get("account").get(
                "auth_type") == _OAUTHFLOW:
        check_refresh_required = (
            # if_session_expired = True means access token expired
            ('check_rest_response', ['{{__response__.status_code}}', '{{__response__.body}}'], 'if_session_expired'),
            # if_session_expired = True means access token refreshed
            ('refresh_access_token', ['{{if_session_expired}}', task_config, meta_config, logger, helper_proxy],
             'is_token_refreshed')
        )
        task.add_postprocess_handler_batch(check_refresh_required)
    post_params = (
        # Set necessary variables for collection of hourly logs
        ('set_var', [hourly], 'hourly'),
        ('set_var', [collection_date], 'collection_date'),

        ('json_path', ['{{__response__.body}}', 'records'], 'records'),
        ('log', [logging.INFO, 'Found {{records|count}} records in response.'], ''),
        ('set_var', ['{{records|count==0}}'], 'result_empty'),
        ('exclude_fields', ['{{records}}', '{{hourly}}'], 'records'),
        ('json_path', ['{{records}}', '[-1].{{collection_date}}'], 'new_start_date'),
        (
            'extract_ids_on_date', ['{{records}}', '{{new_start_date}}', '{{records_on_start_date}}', '{{hourly}}'],
            'records_on_last_date'
        ),
        ('filter_not_indexed_records', ['{{records}}', '{{records_on_start_date}}'], 'records'),
        ('log', [logging.INFO, 'Got {{records|count}} records after filtered.'], ''),

        ('set_var', ['{{records_on_last_date}}'], 'records_on_start_date'),
        (
            'refresh_start_date',
            ['{{comparator}}', '{{previous_empty}}', '{{start_date}}', '{{next_start_date}}', '{{new_start_date}}'],
            'start_date'
        ),
        ('set_var', ['{{records|count>0}}'], 'records_not_empty'),
        ('set_var', ['{{records|count==0}}'], 'records_empty'),
    )
    task.add_postprocess_handler_batch(post_params)
    # In case of oAuthflow fetch user_account_id from UserInfoEndpoint
    if task_config.get("account").get("auth_type") \
            and task_config.get("account").get("auth_type") == _OAUTHFLOW:
        task.add_postprocess_handler('get_account_id', [task_config, meta_config, logger, helper_proxy], '')

@cce_pipeline_plugin
def _list_event_log(task_config, meta_config, logger, helper_proxy=None, is_retry=False, session_active=True):
    if session_active:
        task = common.get_sfdc_task_template('EventLog', task_config, meta_config)
        task.set_iteration_count(2)
        task.configure_checkpoint(
            name='{{name}}',
            content={
                'start_date': '{{start_date}}',
                'start_date_config': '{{start_date_config}}',
                'records': '{{records}}',
                'records_on_start_date': '{{records_on_start_date}}',
            }
        )
        # In case of OAuth flow skip checking login result
        if (not task_config.get("account").get("auth_type")) or task_config.get("account").get(
                "auth_type") != _OAUTHFLOW:
            common.check_login_result(task)
        add_process_pipeline(task, task_config, meta_config, logger, helper_proxy, is_retry)
        return task


def _split_records_to_file():
    """Split the EventLog file records to file downloading tasks"""
    task = CCESplitTask(name='EventLogRecordsToFiles')
    task.configure_split(
        method='split_by',
        source='{{records}}',
        output='event_log_file'
    )
    return task


def collect_events(helper, ew):
    """Collect events"""
    stanza_name = helper.get_input_stanza_names()
    logger = common.setup_logger(stanza_name, helper.get_log_level())
    logger.info('Collecting events started.')

    task_config = helper.get_input_stanza(stanza_name)
    meta_config = helper._input_definition.metadata
    if not common.check_common_parameters(task_config, logger):
        rest.simpleRequest("messages",
                           meta_config['session_key'],
                           postargs={"severity": "error",
                                     "name": "SFDC error message",
                                     "value": "Configurations are incomplete for Salesforce inputs. "
                                     "Go to the Salesforce Add-on [[/app/Splunk_TA_salesforce/inputs|Inputs page]] to complete them and to begin or to resume data collection."
                                    },
                           method="POST")
        return

    meta_config['checkpoint_dir'] = common.reset_checkpoint_dir(
        meta_config['checkpoint_dir'], task_config['name'], logger
    )

    task_config.update({
        'appname': helper.get_app_name(),
        'stanza_name': stanza_name
    })

    # Query start date provided by user from inputs
    start_date_config = task_config.get('start_date')
    # Fix query start date to default if not provided or provided in invalid format
    start_date_config_fixed = common.fix_start_date(start_date_config, _DEFAULT_START_DATE, logger)

    # Fetch checkpoint
    ckpt_manager = TACheckPointMgr(meta_config, task_config)
    ckpt_data = ckpt_manager.get_ckpt([stanza_name])
    if ckpt_data:
        # Query start date provided by user from checkpoint
        ckpt_start_date_config = ckpt_data.get('start_date_config')
        ckpt_start_date_updated = None

        # if checkpoint is present and user has updated Query Start date to a valid or empty value
        if ckpt_start_date_config != None and \
            common.is_start_date_changed(start_date_config, ckpt_start_date_config) and \
            (start_date_config == start_date_config_fixed or start_date_config == ""):
            # Store user provided query start date in checkpoint. Reset Checkpoint
            logger.info('Query start date modified. Resetting checkpoint. Starting collection from %s', start_date_config_fixed)
            ckpt_start_date_config_updated = common.config_to_ckpt_date_str(start_date_config)
            ckpt_start_date_updated = common.config_to_ckpt_date_str(start_date_config_fixed)
            ckpt_records_updated = []
            ckpt_records_on_start_date_updated = []

        # if start_date_config is not defined in checkpoint or start_date is updated to an invalid value
        elif not ckpt_start_date_config or (start_date_config != start_date_config_fixed and \
                                            str(start_date_config) != str(ckpt_start_date_config)):
            if ckpt_start_date_config:
                logger.info('Query start date modified. Invalid value found. Resuming collection from checkpoint')
            else:
                logger.debug('Last known Query Start Date will be updated in checkpoint.')
            # Store user provided query start date in checkpoint. Continue from existing checkpoint
            ckpt_start_date_config_updated = common.config_to_ckpt_date_str(str(start_date_config))
            ckpt_start_date_updated = ckpt_data.get('start_date')
            ckpt_records_updated = ckpt_data.get('records')
            ckpt_records_on_start_date_updated = ckpt_data.get('records_on_start_date')

        if ckpt_start_date_updated:
            ckpt={
                'start_date': ckpt_start_date_updated,
                'start_date_config': ckpt_start_date_config_updated,
                'records': ckpt_records_updated,
                'records_on_start_date': ckpt_records_on_start_date_updated
            }
            ckpt_manager = TACheckPointMgr(meta_config, task_config)
            ckpt_manager.update_ckpt(ckpt, None)
    else:
        logger.debug('No existing checkpoint found.')

    task_config.update({
        'limit': _DEFAULT_LIMIT,
        'API_VERSION': 'v' + task_config.get("account").get("sfdc_api_version"),
        'start_date': start_date_config_fixed,
        'is_greater_than': 'true',
        'start_date_config': common.config_to_ckpt_date_str(start_date_config),
        'session':task_config.get("account").get("access_token")
    })
    # Block for OAuth flow
    if task_config.get("account").get("auth_type") and task_config.get("account").get("auth_type") == _OAUTHFLOW:
        set_values = (
            ('set_var', ['{{session}}'], 'session_id'),
            ('set_var', ['{{account.instance_url}}'], 'server_url')
        )
        task = _list_event_log(task_config, meta_config, logger, helper.proxy, False, True)
        task.add_preprocess_handler_batch(set_values)
        tasks = (
            task,
            _split_records_to_file(),
            _index_event_log_file(task_config, meta_config)
        )
        common.run_tasks(tasks, logger, ctx=task_config, proxy=helper.proxy)
    else:
        # Block for normal flow
        tasks = (
            common.login_sfdc(),
            _list_event_log(task_config, meta_config, logger),
            _split_records_to_file(),
            _index_event_log_file(task_config, meta_config)
        )
        common.run_tasks(tasks, logger, ctx=task_config, proxy=helper.proxy)

    logger.info('Collecting events finished.')
