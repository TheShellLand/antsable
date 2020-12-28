import import_declare_test
import splunk.admin as admin
from solnlib import log
from framework import state_store as ss
from solnlib.splunkenv import make_splunkhome_path
import traceback


log.Logs.set_context()
_LOGGER = log.Logs().get_logger('ta_snow_data_input_checkpoint')

class CheckpointHandler(admin.MConfigHandler):
    def setup(self):
        self.supportedArgs.addReqArg("input_name")
        return
   
    @staticmethod
    def get_session_key(self):
        return self.getSessionKey()
    
    """
    This handler is to get checkpoint of data input
    It takes 'input_name' as caller args and
    Returns the confInfo dict object in response.
    """
    def handleList(self, confInfo):
        try:
            _LOGGER.debug("In checkpoint handler to get checkpoint of data input")
            # # Get args parameters from the request
            _LOGGER.info("self.callerArgs.data: {}".format(self.callerArgs.data))
            input_name = self.callerArgs.data['input_name'][0]
            session_key = self.get_session_key(self)
            appname = "Splunk_TA_snow"
            metadata = {
                'checkpoint_dir': make_splunkhome_path(["var", "lib", "splunk", "modinputs", "snow"]),
                'session_key': session_key
            }
            state = ss.StateStore(metadata, appname)
            checkpoint_data = state.get_state(input_name)

            _LOGGER.info("Checkpoint data: {}".format(checkpoint_data))
            if checkpoint_data:
                _LOGGER.info("Found checkpoint for {}".format(input_name))
                confInfo['token']['checkpoint_exist'] = True
            else:
                _LOGGER.info("Checkpoint not found of {}".format(input_name))
                confInfo['token']['checkpoint_exist'] = False
        
        except Exception as exc:
            _LOGGER.error("Error {}".format(traceback.format_exc()))
        return

if __name__ == '__main__':
    admin.init(CheckpointHandler, admin.CONTEXT_APP_AND_USER)
