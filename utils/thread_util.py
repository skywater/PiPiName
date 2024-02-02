import threading
import utils.common_util as util
# log = fu.get_logger(__file__)
tld = threading.local()
tld.log, tld.data = None, None


def get_log(log_file=None):
    if tld.log is None:
        tld.log = util.get_logger(__file__ if log_file is None else log_file)
    return tld.log


def get_val():
    return tld.data


def set_val(value, log_file=None):
    tld.data = value
    if tld.log is None:
        tld.log = util.get_logger(__file__ if log_file is None else log_file)


def clear(is_log=False):
    """
    线程隔离，只会释放当前线程资源 \n
    del tld 会直接报错 UnboundLocalError: local variable 'tld' referenced before assignment
    :return:
    """
    if is_log:
        get_log().info(f"清除当前线程变量={tld.data}")
    delattr(tld, 'data')
    delattr(tld, 'log')
