import os.path as op
import sys

sys.path.insert(0, op.dirname(op.dirname(op.abspath(__file__))))

import snow_event_base as seb

# encoding = utf-8

class ModSnowEvent(seb.SnowEventBase):

    def __init__(self, payload):
        self._payload = payload
        self._payload["configuration"]["additional_info"] = payload["results_link"]
        self._session_key = payload["session_key"]
        self.account = payload["configuration"]["account"]
        super(ModSnowEvent, self).__init__()

    def _get_session_key(self):
        return self._session_key

    def _get_events(self):
        return (self._payload["configuration"],)


def process_event(helper, *args, **kwargs):

    # Initialize the class and execute the code for alert action
    helper.log_info("Alert action snow_event started.")
    handler = ModSnowEvent(helper.settings)
    handler.handle()

    return 0
