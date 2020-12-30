import sys
import json
import hashlib
import traceback

import snow_incident_base as sib


class ModSnowIncident(sib.SnowIncidentBase):

    def __init__(self, payload):
        self._payload = payload
        self._configuration = payload["configuration"]
        self._configuration["splunk_url"] = payload["results_link"]
        # FIXME Should refactor base class
        self._configuration["ciIdentifier"] = self._configuration.get("configuration_item", "")
        super(ModSnowIncident, self).__init__()

    def _get_session_key(self):
        return self._payload["session_key"]

    def _get_correlation_id(self, event):
        unique_name = "/".join((self._payload["search_name"],
                                self._payload["owner"],
                                self._payload["app"]))
        return hashlib.md5(unique_name).hexdigest()

    def _get_events(self):
        return self._configuration,


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        try:
            raw_payload = sys.stdin.read()
            payload = json.loads(raw_payload)
            handler = ModSnowIncident(payload)
            handler.handle()
        except Exception:
            print >> sys.stderr, "ERROR Unexpected error: {}".format(
                traceback.format_exc())
            sys.exit(3)
    else:
        print >> sys.stderr, ("FATAL Unsupported execution mode "
                              "(expected --execute flag)")
        sys.exit(1)
