import datetime
import os
import os.path as op
import xml.sax.saxutils as xss


def make_splunkhome_path(parts):
    """
    @parts: path relative to splunk home
    """

    home = os.environ.get("SPLUNK_HOME", ".")
    fullpath = op.normpath(op.join(home, *parts))
    return fullpath


def get_splunk_bin():
    if os.name == "nt":
        splunk_bin = "splunk.exe"
    else:
        splunk_bin = "splunk"
    return make_splunkhome_path(("bin", splunk_bin))


def get_appname_from_path(absolute_path):
    parts = absolute_path.split(op.sep)
    parts.reverse()
    try:
        idx = parts.index("apps")
    except ValueError:
        return None
    else:
        try:
            if parts[idx + 1] == "etc":
                return parts[idx - 1]
            return None
        except IndexError:
            return None


def handle_tear_down_signals(callback):
    import signal

    signal.signal(signal.SIGTERM, callback)
    signal.signal(signal.SIGINT, callback)

    if os.name == "nt":
        signal.signal(signal.SIGBREAK, callback)


def datetime_to_seconds(dt):
    epoch_time = datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch_time).total_seconds()


def is_true(val):
    value = str(val).strip().upper()
    if value in ("1", "TRUE", "T", "Y", "YES"):
        return True
    return False


def is_false(val):
    value = str(val).strip().upper()
    if value in ("0", "FALSE", "F", "N", "NO", "NONE", ""):
        return True
    return False


def remove_http_proxy_env_vars():
    for k in ("http_proxy", "https_proxy"):
        if k in os.environ:
            del os.environ[k]
        elif k.upper() in os.environ:
            del os.environ[k.upper()]


def escape_cdata(data):
    data = data.encode("utf-8", errors="xmlcharrefreplace")
    data = xss.escape(data)
    return data
