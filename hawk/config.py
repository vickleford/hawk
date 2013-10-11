import yaml
from os.path import expanduser

with open(expanduser('~/.config/hawk.yaml')) as f:
    config = yaml.load(f)