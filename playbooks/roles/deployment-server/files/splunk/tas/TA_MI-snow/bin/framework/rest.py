import urllib
import json
from traceback import format_exc
import sys
import os.path as op

sys.path.insert(0, op.dirname(op.dirname(op.abspath(__file__))))

import framework.utils as utils
from httplib2 import (socks, ProxyInfo, Http)

import framework.log as log
import framework.ta_consts as c


_LOGGER = log.Logs().get_logger(c.ta_util)


def splunkd_request(splunkd_uri, session_key, method="GET",
                    headers=None, data=None, timeout=30, retry=1):
    """
    @return: httplib2.Response and content
    """

    headers = headers if headers is not None else {}
    headers["Authorization"] = "Splunk {0}".format(session_key)
    content_type = headers.get("Content-Type")
    if not content_type:
        content_type = headers.get("content-type")

    if not content_type:
        content_type = "application/x-www-form-urlencoded"
        headers["Content-Type"] = content_type

    if data is not None:
        if content_type == "application/json":
            data = json.dumps(data)
        else:
            data = urllib.urlencode(data)

    http = Http(timeout=timeout, disable_ssl_certificate_validation=True)
    msg_temp = "Failed to send rest request=%s, errcode=%s, reason=%s"
    resp, content = None, None
    for _ in range(retry):
        try:
            resp, content = http.request(splunkd_uri, method=method,
                                         headers=headers, body=data)
        except Exception:
            _LOGGER.error(msg_temp, splunkd_uri, "unknown", format_exc())
        else:
            if resp.status not in (200, 201):
                _LOGGER.error(msg_temp, splunkd_uri, resp.status,
                              code_to_msg(resp, content))
            else:
                return resp, content
    else:
        return resp, content


def code_to_msg(resp, content):
    code_msg_tbl = {
        400: "Request error. reason={}".format(content),
        401: "Authentication failure, invalid access credentials.",
        402: "In-use license disables this feature.",
        403: "Insufficient permission.",
        404: "Requested endpoint does not exist.",
        409: "Invalid operation for this endpoint. reason={}".format(content),
        500: "Unspecified internal server error. reason={}".format(content),
        503: ("Feature is disabled in the configuration file. "
              "reason={}".format(content)),
    }

    return code_msg_tbl.get(resp.status, content)


def build_http_connection(config, timeout=120):
    """
    @config: dict like, proxy and account information are in the following
             format {
                 "username": xx,
                 "password": yy,
                 "proxy_url": zz,
                 "proxy_port": aa,
                 "proxy_username": bb,
                 "proxy_password": cc,
                 "proxy_type": http,http_no_tunnel,sock4,sock5,
                 "proxy_rdns": 0 or 1,
             }
    @return: Http2.Http object
    """

    proxy_type_to_code = {
        "http": socks.PROXY_TYPE_HTTP,
        "http_no_tunnel": socks.PROXY_TYPE_HTTP_NO_TUNNEL,
        "socks4": socks.PROXY_TYPE_SOCKS4,
        "socks5": socks.PROXY_TYPE_SOCKS5,
    }
    if config.get("proxy_type") in proxy_type_to_code:
        proxy_type = proxy_type_to_code[config["proxy_type"]]
    else:
        proxy_type = socks.PROXY_TYPE_HTTP

    rdns = utils.is_true(config.get("proxy_rdns"))

    proxy_info = None

    disable_ssl_validation = utils.is_true(config.get("disable_ssl_certificate_validation"))

    if config.get("proxy_url") and config.get("proxy_port"):
        if config.get("proxy_username") and config.get("proxy_password"):
            proxy_info = ProxyInfo(proxy_type=proxy_type,
                                   proxy_host=config["proxy_url"],
                                   proxy_port=int(config["proxy_port"]),
                                   proxy_user=config["proxy_username"],
                                   proxy_pass=config["proxy_password"],
                                   proxy_rdns=rdns)
        else:
            proxy_info = ProxyInfo(proxy_type=proxy_type,
                                   proxy_host=config["proxy_url"],
                                   proxy_port=int(config["proxy_port"]),
                                   proxy_rdns=rdns)
    http = Http(proxy_info=proxy_info, timeout=timeout,
                disable_ssl_certificate_validation=disable_ssl_validation)
    if config.get("username") and config.get("password"):
        http.add_credentials(config["username"], config["password"])
    return http
