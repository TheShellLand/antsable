ta_frmk = "ta_frmk"
ta_frmk_conf = "ta_frmk_conf"
ta_frmk_rest = "ta_frmk_rest"
ta_frmk_state_store = "ta_frmk_state_store"


def get_all_logs():
    g = globals()
    return [g[log] for log in g if log.startswith("ta_")]
