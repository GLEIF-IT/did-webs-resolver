# Logging config
import logging

from hio.help import ogling

from dkr.app.logs import TruncatedFormatter

log_name = 'dws'  # name of this project that shows up in log messages

ogler = ogling.initOgler(prefix=log_name, syslogged=False)
ogler.level = logging.INFO
formatter = TruncatedFormatter(f'%(asctime)s [{log_name}] %(levelname)-8s %(module)s.%(funcName)s-%(lineno)s %(message)s')
formatter.default_msec_format = None
ogler.baseConsoleHandler.setFormatter(formatter)
ogler.reopen(name=log_name, temp=True, clear=True)

# Versioning
__version__ = '0.2.1'  # also change in pyproject.toml
