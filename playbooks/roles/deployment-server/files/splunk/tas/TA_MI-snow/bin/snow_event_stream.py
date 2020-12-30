import snow_event_base as seb
import splunk.Intersplunk as si


class SnowEventStream(seb.SnowEventBase):

    def _get_events(self):
        return si.readResults(None, None, True)


def main():
    handler = SnowEventStream()
    handler.handle()


if __name__ == "__main__":
    main()
