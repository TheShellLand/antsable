# encoding = utf-8
import import_declare_test

import datetime
import hashlib
import os
import os.path as op
import signal
import time
from solnlib import conf_manager
from cloudconnectlib.core.engine_v2 import CloudConnectEngine
from cloudconnectlib.core.job import CCEJob
from cloudconnectlib.core.task import CCEHTTPRequestTask
from cloudconnectlib.core.plugin import cce_pipeline_plugin
from cloudconnectlib.core.ext import regex_search

_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S.000z'
CONFIG_START_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.000z'
CKPT_START_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.000+0000'
_OAUTHFLOW = "oauth"

SERVER_URL_REGEX = ('\<serverUrl\>(?P<serverUrl>https:\/\/[a-zA-Z0-9\-\.]+)\/.*\<\/serverUrl\>')
SESSION_ID_REGEX = '\<sessionId\>(?P<sessionId>.*)\<\/sessionId\>'
_ERROR_CODE_REGEX = '"errorCode":"(?P<errorcode>.*)"'
_ERROR_MESSAGE_REGEX = '"message":"(?P<message>.*)",'
_ACCESS_TOKEN_REGEX = '"access_token":"(?P<accesstoken>.*?)"'
_USER_ID_REGEX = '"user_id":"(?P<userid>.*?)"'
_USER_ID_BASIC_REGEX = '\<userId\>(?P<userid>.*?)\<\/userId\>'

UNAUTHORIZED_STATUS = '401'
INVALID_SESSION_ID = 'INVALID_SESSION_ID'


def setup_logger(stanza_name, log_level):
    """Setup Cloud Connect Engine logger level and prefix"""
    from cloudconnectlib.common.log import reset_cc_logger
    log_prefix = '[stanza_name={}]'.format(stanza_name)
    return reset_cc_logger(stanza_name, log_level, log_prefix)


def signup_exit_signal(task):
    """Signup exit signal handler for task"""

    def signal_handler(signal, frame):
        task.stop()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


def get_sfdc_task_template(task_name, task_config, meta_config):
    header = {'Authorization': 'Bearer {{session_id}}'}
    return CCEHTTPRequestTask(
        request={
            'url': '{{server_url}}/services/data/v%s/query?q={{query_string}}' % task_config.get("account").get("sfdc_api_version"),
            'method': 'GET',
            'headers': header,
        },
        name=task_name,
        meta_config=meta_config,
        task_config=task_config
    )


def login_sfdc():
    rq_body = ('<?xml version="1.0" encoding="utf-8" ?>'
               '<env:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
               ' xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">'
               '<env:Body>'
               '<n1:login xmlns:n1="urn:partner.soap.sforce.com">'
               '<n1:username>{{account.username}}</n1:username>'
               '<n1:password><![CDATA[{{account.password}}]]>{{account.token}}</n1:password>'
               '</n1:login></env:Body>'
               '</env:Envelope>')
    header = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'login'
    }
    task = CCEHTTPRequestTask(
        request={
            'url': 'https://{{account.endpoint}}/services/Soap/u/{{account.sfdc_api_version}}/',
            'method': 'POST',
            'headers': header,
            'body': rq_body
        },
        name='Login'
    )
    task.set_iteration_count(1)

    extract_values = (
        ('regex_search', [SESSION_ID_REGEX, '{{__response__.body}}'], 'session'),
        ('set_var', ['{{session.sessionId}}'], 'session_id'),
        ('regex_search', [SERVER_URL_REGEX, '{{__response__.body}}'], 'server'),
        ('set_var', ['{{server.serverUrl}}'], 'server_url'),
        ('regex_search', [_USER_ID_BASIC_REGEX, '{{__response__.body}}'], 'user_id'),
        ('set_var', ['{{user_id.userid}}'], 'user_account_id'),
    )
    task.add_postprocess_handler_batch(extract_values)
    return task


def _get_days_ago_timestamp(num_days):
    date = datetime.date.today() - datetime.timedelta(days=num_days)
    return date.strftime(_TIMESTAMP_FORMAT)


def fix_start_date(start_date, num_days_ago, logger):
    timestamp = _get_days_ago_timestamp(num_days_ago)
    if not start_date:
        logger.info(
            "Query start date is not provided"
        )
        return timestamp
    try:
        time.strptime(start_date, _TIMESTAMP_FORMAT)
    except ValueError:
        logger.warning(
            "Query start date provided is in invalid format."
        )
        return timestamp
    return start_date


def run_tasks(tasks, logger, ctx, proxy):
    """Add tasks to Job and run job in Cloud Connect Engine"""
    job = CCEJob(context=ctx)
    if proxy:
        logger.info("Proxy is enabled. Using the proxy settings.")
        proxy['proxy_enabled'] = True
        job.set_proxy(proxy)

    for task in tasks:
        job.add_task(task)

    engine = CloudConnectEngine()
    engine.start(jobs=(job,))


def check_login_result(task):
    # Error handling, print the fault string or default error message
    # if login failed
    steps = (
        ('check_login_result', ['{{session_id}}', '{{server_url}}', '{{__response__.body}}'], 'login_failed'),
        ('exit_job_if_true', ['{{login_failed}}'], '')
    )
    task.add_preprocess_handler_batch(steps)


def reset_checkpoint_dir(checkpoint_dir, input_name, logger):
    try:
        if not op.exists(checkpoint_dir):
            logger.debug('Checkpoint directory not found. Creating checkpoint directory %s', checkpoint_dir)
            os.mkdir(checkpoint_dir)
        # Hash input name to avoid input name length exceed limit
        hashed_folder = hashlib.sha256(input_name.encode("utf-8")).hexdigest()
        new_checkpoint_dir = op.join(checkpoint_dir, hashed_folder)
        if not op.exists(new_checkpoint_dir):
            logger.debug('Sub-directory not found for stanza %s. Creating sub-directory as %s in checkpoint directory %s', input_name, hashed_folder, checkpoint_dir)
            os.mkdir(new_checkpoint_dir)
        return new_checkpoint_dir
    except Exception:
        logger.warning('Cannot create sub folder in checkpoint dir %s for stanza %s', checkpoint_dir, input_name)
    return checkpoint_dir


def check_common_parameters(task_conf, logger):
    if not task_conf.get("account"):
        logger.warning('Salesforce account is not configured for input "%s". Add-on is going to exit.', task_conf.get("name"))
        return False
    if not task_conf.get("account").get("auth_type"):
        logger.warning('Salesforce account is misconfigured for input "%s". Please reconfigure account "%s". Add-on is going to exit.',
                       task_conf.get("name"), task_conf.get("account").get("name"))
        return False
    elif task_conf.get("account").get("auth_type") == _OAUTHFLOW:
        for key in ('endpoint', 'access_token', 'client_id', 'client_secret', 'instance_url', 'refresh_token'):
            if not task_conf.get("account").get(key) or task_conf.get("account").get(key) == '':
                logger.warning('Salesforce %s is not configured for account "%s". Add-on is going to exit.', key, task_conf.get("account").get("name"))
                return False
    else:
        for key in ('endpoint', 'username', 'password'):
            if not task_conf.get("account").get(key) or task_conf.get("account").get(key) == '':
                logger.warning('Salesforce %s is not configured for account "%s". Add-on is going to exit.', key, task_conf.get("account").get("name"))
                return False

    if task_conf.get("account").get("sfdc_api_version") not in ['42.0','43.0','44.0','45.0','46.0','47.0','48.0']:
        logger.error('Salesforce api version is misconfigured for account "%s". Please reconfigure account "%s". Add-on is going to exit.', task_conf.get("account").get("name"), task_conf.get("account").get("name"))
        return False

    return True

def get_ckpt_date_obj(start_date_string):
    try:
        return time.strptime(start_date_string, CKPT_START_DATE_FORMAT)
    except:
        return None

def get_config_date_obj(start_date_string):
    try:
        return time.strptime(start_date_string, CONFIG_START_DATE_FORMAT)
    except:
        return None

def config_to_ckpt_date_str(start_date_string):
    try:
        start_date = time.strptime(start_date_string, CONFIG_START_DATE_FORMAT)
        return time.strftime(CKPT_START_DATE_FORMAT, start_date)
    except:
        # If invalid or empty, return the date string as it is
        return start_date_string

def is_start_date_changed(start_date_config, ckpt_start_date_config):
    # if user has changed the start_date
    if get_config_date_obj(start_date_config) != get_ckpt_date_obj(ckpt_start_date_config):
        return True
    # when user updates from invalid start_date to another invalid value or empty value
    elif not (get_config_date_obj(start_date_config) or get_ckpt_date_obj(ckpt_start_date_config)) and \
         str(start_date_config) != str(ckpt_start_date_config):
        return True
    return False

# This method is to check for AuthError for access token
@cce_pipeline_plugin
def check_rest_response(status, response):
    error = regex_search(_ERROR_CODE_REGEX, response) if response else {}
    error_code = error.get("errorcode", "")
    if status == UNAUTHORIZED_STATUS and error_code == INVALID_SESSION_ID:
        return True
    else:
        return False


# This method is to refresh the access token if required
@cce_pipeline_plugin
def refresh_access_token(is_access_token_expired, task_config, meta_config, logger, helper_proxy):
    if is_access_token_expired:
        logger.debug("Access token expired. Refreshing access token")
        rq_body = "grant_type=refresh_token" \
                  "&client_id="+task_config.get("account").get("client_id") +\
                  "&client_secret="+task_config.get("account").get("client_secret") +\
                  "&refresh_token="+task_config.get("account").get("refresh_token")
        header = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        task = CCEHTTPRequestTask(
            request={
                'url': 'https://'+task_config.get("account").get("endpoint")+'/services/oauth2/token',
                'method': 'POST',
                'headers': header,
                'body': rq_body
            },
            name='Login',
            meta_config=meta_config,
            task_config=task_config
        )
        task.set_iteration_count(1)
        extract_values = (
            ('regex_search', [_ACCESS_TOKEN_REGEX, '{{__response__.body}}'], 'access_token'),
            ('set_var', ['{{access_token.accesstoken}}'], 'session_id'),
            ('set_var', ['{{session_id}}'], 'session'),
            ('update_access_token', ['{{access_token.accesstoken}}','{{account.client_secret}}',
                                     '{{account.refresh_token}}', meta_config.get("session_key"), '{{appname}}',
                                     '{{account.name}}'], '')
        )
        task.add_postprocess_handler_batch(extract_values)
        run_tasks((task,), logger, ctx=task_config, proxy=helper_proxy)
        return True
    else:
        logger.debug("Access token not expired")
        return False


# This method is for updating the accesstoken in conf file
@cce_pipeline_plugin
def update_access_token(access_token, client_secret, refresh_token, splunk_session_key, app_name, stanza_name):
    cfm = conf_manager.ConfManager(splunk_session_key, app_name, realm= "__REST_CREDENTIAL__#Splunk_TA_salesforce#configs/conf-splunk_ta_salesforce_account")
    conf = cfm.get_conf('splunk_ta_salesforce_account')
    conf.update(stanza_name,
                {'access_token': access_token, 'client_secret': client_secret, 'refresh_token': refresh_token},
                ['access_token', 'client_secret', 'refresh_token'])
    return True


# This method is to fetch the user_account_id in case of oauth flow
@cce_pipeline_plugin
def get_account_id(task_config, meta_config, logger, helper_proxy):
    logger.debug("Fetching User Account Id.")
    header = {
        'Authorization': 'Bearer {{session_id}}',
        'Accept': 'application/json'}
    task = CCEHTTPRequestTask(
        request={
            'url': '{{server_url}}/services/oauth2/userinfo',
            'method': 'POST',
            'headers': header
        },
        name='GetUserAccountId',
        meta_config=meta_config,
        task_config=task_config
    )
    task.set_iteration_count(1)
    extract_values = (
        ('regex_search', [_USER_ID_REGEX, '{{__response__.body}}'], 'user_id'),
        ('set_var', ['{{user_id.userid}}'], 'user_account_id')
    )
    task.add_postprocess_handler_batch(extract_values)
    run_tasks((task,), logger, ctx=task_config, proxy=helper_proxy)
    return True
