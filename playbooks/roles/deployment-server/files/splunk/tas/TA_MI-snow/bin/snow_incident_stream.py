import snow_incident_base as sib
import splunk.Intersplunk as si


class SnowIncidentStream(sib.SnowIncidentBase):

    def _get_events(self):
        return si.readResults(None, None, True)


def main():
    handler = SnowIncidentStream()
    handler.handle()


if __name__ == "__main__":
    main()
