# encoding = utf-8
import import_declare_test

import logging

import sfdc_common as common
from cloudconnectlib.core.ext import regex_search
from splunktaucclib.rest_handler import util
from splunk import rest
from cloudconnectlib.core.plugin import cce_pipeline_plugin
from cloudconnectlib.splunktacollectorlib.data_collection.ta_checkpoint_manager import TACheckPointMgr

util.remove_http_proxy_env_vars()

_DEFAULT_START_DATE = 90
_DEFAULT_QUERY_LIMIT = 1000
_OAUTHFLOW = "oauth"


def validate_input(helper, definition):
    # Do not validate input because we cannot get all fields in input sometimes.
    # For instance, if we add a stanza to inputs.conf, and one of the fields is
    # raw text and need to encrypted, when modular input process start, it will
    # read input through UCC and UCC will auto-encrypt this field. The problem is
    # UCC will only submit this field, and then Splunk validation triggered. Only
    # one field passed here.
    pass


def _format_query(task):
    """Build and quote the query string"""
    task.add_preprocess_handler(
        'build_query',
        ['{{is_greater_than}}', '{{object}}', '{{object_fields}}', '{{order_by}}', '{{limit}}', '{{start_date}}', '{{sorting_order}}'],
        'query_string'
    )
    task.add_preprocess_handler('log', [logging.DEBUG, 'Query event object SOQL={{query_string}}'], '')
    task.add_preprocess_handler('quote', ['{{query_string}}'], 'query_string')


def _fix_source_and_sourcetype(task):
    """Fix source to sfdc_object://<object>_<account_name>_<input_name> and sourcetype to sfdc:<object>"""
    task.add_postprocess_handler('set_var', ['sfdc_object://{{object}}_{{account_name}}_{{input_name}}'], 'source')
    task.add_postprocess_handler('set_var', ['sfdc:{{object.lower()}}'], 'sourcetype')


def _stream_events(task):
    # Add timestamp for each record
    task.add_postprocess_handler(
        'convert_records_to_events',
        ['{{records}}', '{{order_by}}', '{{index}}', '{{host}}', '{{source}}', '{{sourcetype}}', '{{user_account_id}}'],
        'splunk_events'
    )
    task.add_postprocess_handler('std_output', ['{{splunk_events}}'])
    task.add_postprocess_handler('log', [logging.DEBUG, '{{records|count}} events collected'])


def _configure_checkpoint(task):
    task.configure_checkpoint(
        name='{{name}}',
        content={
            'start_date': '{{start_date}}',
            'is_greater_than': '{{is_greater_than}}',
            'start_date_config': '{{start_date_config}}',
            'sorting_order': '{{sorting_order}}'
        }
    )


@cce_pipeline_plugin
def check_sorting_order(logger, status_code, response):
    error = regex_search(common._ERROR_CODE_REGEX, response) if response else {}
    error_code = error.get("errorcode", "")
    message = regex_search(common._ERROR_MESSAGE_REGEX, response) if response else {}
    message = message.get("message", "")
    if error_code == "BIG_OBJECT_UNSUPPORTED_OPERATION" and message == "Unsupported order direction on filter column: ASCENDING":
        logger.info("sorting order is set to 'DESC'")
        return "DESC"
    return "ASC"

def _add_oauth_refresh_token_tasks(task, task_config, meta_config, logger, helper_proxy):
    check_refresh_required = (
                # if_session_expired = True means access token expired
                ('check_rest_response', ['{{__response__.status_code}}', '{{__response__.body}}'],
                    'if_session_expired'),
                # if_session_expired = True means access token refreshed
                ('refresh_access_token', ['{{if_session_expired}}', task_config, meta_config, logger, helper_proxy],
                    'is_token_refreshed')
                )
    task.add_postprocess_handler_batch(check_refresh_required)


def validate_sort_order(task_config, meta_config, logger, helper_proxy=None):
    task = common.get_sfdc_task_template('IdentifySortOrder', task_config, meta_config)
    task.set_iteration_count(0)
    common.signup_exit_signal(task)
    # In case of OAuth flow skip the checking of login result
    if task_config.get("account").get("auth_type") != _OAUTHFLOW:
        common.check_login_result(task)
    task.add_preprocess_handler('set_var',[False],'is_token_refreshed')
    task.add_preprocess_handler('exit_if_true', ["{{sorting_order_validation_done}}"])
    _format_query(task)

    # In case of OAuth flow add tasks for refresh access token
    if task_config.get("account").get("auth_type") == _OAUTHFLOW:
        _add_oauth_refresh_token_tasks(task, task_config, meta_config, logger, helper_proxy)

    task.add_postprocess_handler('check_sorting_order', [logger, '{{__response__.status_code}}', '{{__response__.body}}'], 'sorting_order')
    task.add_postprocess_handler('set_var', [True], 'sorting_order_validation_done')
    return task

@cce_pipeline_plugin
def list_objects(task_config, meta_config,  logger, helper_proxy=None):
    task = common.get_sfdc_task_template('ListRecords', task_config, meta_config)
    task.set_iteration_count(0)
    common.signup_exit_signal(task)
    _configure_checkpoint(task)
    # In case of OAuth flow skip the checking of login result
    if task_config.get("account").get("auth_type") != _OAUTHFLOW:
        common.check_login_result(task)
    _fix_source_and_sourcetype(task)

    task.add_preprocess_handler('set_var',[False],'is_token_refreshed')
    task.add_preprocess_handler('exit_if_true', ["{{finished and finished.lower() == 'true'}}"])

    _format_query(task)

    # In Case of oAuthflow check for authorization error and refresh the access token if required
    if task_config.get("account").get("auth_type") == _OAUTHFLOW:
        _add_oauth_refresh_token_tasks(task, task_config, meta_config, logger, helper_proxy)

    # Get account name to append in source
    task.add_preprocess_handler('set_var', [task_config.get("account").get("name")], 'account_name')
    # Get input name to append in source
    task.add_preprocess_handler('set_var', [task_config.get("stanza_name")], 'input_name')
    task.add_postprocess_handler('json_path', ['{{__response__.body}}', 'records'], 'records')
    # In case of oAuthflow fetch user_account_id from UserInfoEndpoint
    if task_config.get("account").get("auth_type") == _OAUTHFLOW:
        task.add_postprocess_handler('get_account_id', [task_config, meta_config, logger, helper_proxy], '')

    task.add_postprocess_handler('json_path', ['{{records}}',  '[{{(-1) if  sorting_order== "ASC" else 0}}].{{order_by}}'], 'new_start_date')
    task.add_postprocess_handler('set_var', ['{{not records}}'], 'finished')

    # Filter records which timestamp is not the last timestamp
    task.add_postprocess_handler(
        'filter_records_before_date',
        ['{{is_greater_than}}', '{{records}}', '{{order_by}}', '{{new_start_date}}'], 'records'
    )

    _stream_events(task)

    task.add_postprocess_handler(
        'set_var',
        ["{{false if is_greater_than.lower() == 'true' and finished.lower() == 'false' else true}}"],
        'is_greater_than'
    )
    task.add_postprocess_handler('set_var', ['{{new_start_date or start_date}}'], 'start_date')

    # Set the start_date_config to input stanza's Query Start Date to update in checkpoint
    task.add_postprocess_handler('set_var', [task_config.get('start_date_config')], 'start_date_config')

    return task


def _fix_limit(limit, logger):
    dv = _DEFAULT_QUERY_LIMIT
    if limit:
        try:
            limit = int(limit)
            if limit > 0:
                return limit
        except ValueError:
            pass
        logger.warning("Limit '%s' is invalid, replace it with '%s'", limit, dv)
    else:
        logger.info("Limit is not found, assume it to '%s'", dv)
    return dv


def _check_and_set_parameters(task_conf, logger):
    for key in ('order_by', 'object_fields', 'object'):
        if not task_conf.get(key):
            logger.warning('Field "%s" is missing for object input. Add-on is going to exit.', key)
            return False
    order_by = task_conf['order_by'].strip()
    fields = task_conf.get('object_fields', '')

    fields_list = [x.strip() for x in fields.split(',')]
    if order_by not in fields_list:
        logger.info('Appending %s to object fields', order_by)
        fields_list.append(order_by)
    # Filter empty fields
    task_conf['object_fields'] = ','.join(x for x in fields_list if x)
    return True


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
                                     "value": "Some configurations are missing in Splunk Add-on for Salesforce. "
                                              "Go to the Salesforce Add-on [[/app/Splunk_TA_salesforce/configuration|Configuration page]] to fix them in order to resume data collection."
                                    },
                           method="POST")
        return
    if not _check_and_set_parameters(task_config, logger):
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

    if (not ckpt_data) or ckpt_data and not ckpt_data.get('sorting_order'):
        sorting_order_validation = True
        ckpt_sorting_order = "ASC"
    else:
        sorting_order_validation = False
        ckpt_sorting_order = ckpt_data.get('sorting_order')

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

        if ckpt_start_date_updated:
            ckpt = {
                'is_greater_than': 'true',
                'start_date': ckpt_start_date_updated,
                'sorting_order': ckpt_sorting_order,
                'start_date_config': ckpt_start_date_config_updated
            }
            ckpt_manager = TACheckPointMgr(meta_config, task_config)
            ckpt_manager.update_ckpt(ckpt, None)
    else:
        logger.debug('No existing checkpoint found.')

    limit = _fix_limit(task_config.get('limit'), logger)
    task_config.update({
        'start_date': start_date_config_fixed,
        'limit': limit,
        'is_greater_than': 'true',
        'sorting_order': ckpt_sorting_order,
        'start_date_config': common.config_to_ckpt_date_str(start_date_config),
        'session':task_config.get("account").get("access_token")
    })
    # Block for OAuth flow
    if task_config.get("account").get("auth_type") and task_config.get("account").get("auth_type") == _OAUTHFLOW:
        set_values = (
            ('set_var', ['{{session}}'], 'session_id'),
            ('set_var', ['{{account.instance_url}}'], 'server_url')
        )
        if sorting_order_validation:
            tasks = (
                validate_sort_order(task_config, meta_config, logger, helper.proxy),
                list_objects(task_config, meta_config, logger, helper.proxy),
            )
        else:
            tasks = (list_objects(task_config, meta_config, logger, helper.proxy),)
        for task in tasks:
            task.add_preprocess_handler_batch(set_values)
        common.run_tasks(tasks, logger, ctx=task_config, proxy=helper.proxy)
    else:
        # Block for basic flow
        if sorting_order_validation:
            tasks = (
                common.login_sfdc(),
                validate_sort_order(task_config, meta_config, logger, None),
                list_objects(task_config, meta_config, logger)
            )
        else:
            tasks = (
                common.login_sfdc(),
                list_objects(task_config, meta_config, logger)
            )

        common.run_tasks(tasks, logger, ctx=task_config, proxy=helper.proxy)

    logger.info('Collecting events finished.')
