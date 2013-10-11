from rackspace_monitoring.providers import get_driver
from rackspace_monitoring.types import Provider
from keyring import get_password
from config import config


account = raw_input("Account name: ")

Cls = get_driver(Provider.RACKSPACE)
driver = Cls(account, get_password('hawk', account))

