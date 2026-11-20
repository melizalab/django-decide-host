# -*- mode: python -*-
import json

from rest_framework.renderers import BaseRenderer
from rest_framework.utils import encoders


def dumps(obj) -> str:
    """Serialize obj to compact JSON, like DRF's JSONRenderer"""
    return json.dumps(
        obj, cls=encoders.JSONEncoder, ensure_ascii=False, separators=(",", ":")
    )


class NDJSONRenderer(BaseRenderer):
    """Renders newline-delimited JSON, one object per line.

    List views with StreamingNDJSONMixin stream their results directly and do
    not call this renderer. It is used for other responses, like errors.
    """

    media_type = "application/x-ndjson"
    format = "ndjson"
    charset = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""
        if not isinstance(data, list):
            data = [data]
        return "".join(dumps(item) + "\n" for item in data).encode("utf-8")
