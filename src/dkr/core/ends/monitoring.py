import falcon
from keri.help import nowIso8601


class HealthEnd:
    """Health resource for determining that a container is live"""

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_OK
        resp.media = {'message': f'Health is okay. Time is {nowIso8601()}'}
