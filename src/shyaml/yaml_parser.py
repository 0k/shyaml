
import sys
import yaml

from . import common


class Yaml(object):

    @staticmethod
    def dump(value):
        return value if isinstance(value, common.SIMPLE_TYPES) \
          else yaml.dump(value, default_flow_style=False)

    @staticmethod
    def type_name(value):
        return "struct" if isinstance(value, dict) else \
              "sequence" if isinstance(value, (tuple, list)) else \
              type(value).__name__

    @staticmethod
    def load(filename):
        return yaml.load(sys.stdin)
