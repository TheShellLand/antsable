import import_declare_test
from future import standard_library
standard_library.install_aliases()
import snow_event_base as seb
import splunk.Intersplunk as si
import sys
import re


class SnowEventStream(seb.SnowEventBase):

    def __init__(self):
        # set session key
        self.sessionkey = self._set_session_key()

        # read input
        self.res = self._set_events()
        # no events found
        if not self.res:
            exit(0)

        # get account name
        for event in self.res:
            self.account = event.get("account", None)
            if self.account:
                break
        if not self.account:
            self._handle_error('Field "account" is required by ServiceNow '
                               'for creating events')
        super(SnowEventStream, self).__init__()

    def _get_events(self):
        return self.res

    def _set_events(self):
        return si.readResults(sys.stdin, None, True)

    def _set_session_key(self):
        """
            When called as custom search script, splunkd feeds the following
            to the script as a single line
            'authString:<auth><userId>admin</userId><username>admin</username>\
                <authToken>31619c06960f6deaa49c769c9c68ffb6</authToken></auth>'
        """
        import urllib.parse
        session_key = sys.stdin.readline()
        m = re.search("authToken>(.+)</authToken", session_key)
        if m:
            session_key = m.group(1)
        session_key = urllib.parse.unquote(session_key.encode("ascii").decode("ascii"))
        session_key = session_key.encode().decode("utf-8")
        return session_key

    def _get_session_key(self):
        return self.sessionkey

    def _handle_error(self, msg="Failed to create ticket."):
        si.parseError(msg)

def main():
    handler = SnowEventStream()
    handler.handle()


if __name__ == "__main__":
    main()
