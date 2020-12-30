import sys
import json
import traceback

import snow_event_base as seb


class ModSnowEvent(seb.SnowEventBase):

    def __init__(self, payload):
        self._payload = payload
        self._payload["configuration"]["additional_info"] = \
            payload["results_link"]
        super(ModSnowEvent, self).__init__()

    def _get_session_key(self):
        return self._payload["session_key"]

    def _get_events(self):
        return (self._payload["configuration"],)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        try:
            raw_payload = sys.stdin.read()
            payload = json.loads(raw_payload)
            handler = ModSnowEvent(payload)
            handler.handle()
        except Exception:
            print >> sys.stderr, "ERROR Unexpected error: {}".format(
                traceback.format_exc())
            sys.exit(3)
    else:
        print >> sys.stderr, ("FATAL Unsupported execution mode "
                              "(expected --execute flag)")
        sys.exit(1)
