import sys
import simplejson

from . import common


class Json(object):

    @staticmethod
    def dump(value, encoding='utf-8'):
        return value if isinstance(value, common.SIMPLE_TYPES) \
          else simplejson.dumps(value,
                  ensure_ascii=False,
                  indent=2,
                  sort_keys=True).encode(encoding)

    @staticmethod
    def type_name(value):
        return "Object" if isinstance(value, dict) else \
              "Array"   if isinstance(value, (tuple, list)) else \
              "Boolean" if isinstance(value, (bool, )) else \
              "String"  if isinstance(value, (basestring, )) else \
              "null"    if value is None else \
              type(value).__name__

    @staticmethod
    def load(filename, encoding='utf-8'):
        return simplejson.load(sys.stdin, encoding=encoding)
