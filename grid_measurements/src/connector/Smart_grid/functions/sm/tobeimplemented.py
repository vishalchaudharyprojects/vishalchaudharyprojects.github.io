import time

def pruefe_Steuerbefehl_moeglich():
    time.sleep(1)
    state = "possible" # or "not_possible"
    reason = None # or "connunication failure"
    return state, reason

def sende_steuerbefehl_an_Steuerbox():
    time.sleep(5)
    result = "succeeded" # or "failed"
    return result