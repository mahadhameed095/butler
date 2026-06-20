from client.api import APIClient


def list_apps():
    api = APIClient()
    state = api.get_state()
    return state["Apps"]
