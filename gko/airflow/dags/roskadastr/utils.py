import datetime
from json import JSONEncoder


class MyEncoder(JSONEncoder):
    """JSONEncoder for types."""
    def default(self, obj):

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        return JSONEncoder.default(self, obj)