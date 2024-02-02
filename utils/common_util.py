import array
import base64
import copy
import glob
import inspect
import logging
import os
import re
import time
from collections.abc import Iterable, Mapping, Collection, Set as AbcSet
from typing import overload, Union

import chardet
import magic
# import sys
from pyinstrument import Profiler
from objprint import op
import utils.file_util as fu
import utils.thread_util as tu
LOG_STYLE = '%(asctime)s [%(threadName)s] [%(levelname)s] %(filename)s %(funcName)s:%(lineno)d %(message)s'
# log = None


def chdir_to_cur(file_path=__file__):
    # print("    该文件路径：", ) # 该文件路径： f:\cloud\code\python\quant\py_quant\src\hello-world.py
    # print("该文件绝对路径：", os.path.abspath(filePath)) # 该文件路径： f:\cloud\code\python\quant\py_quant\src\hello-world.py
    # print("  当前项目地址：", os.getcwd()) # 当前项目目录： F:\cloud\code\python\quant\py_quant
    BASE_DIR = os.path.dirname(os.path.abspath(file_path))  # 这里保险的就是直接先把绝对路径加入到搜索路径
    # print("    该文件目录：", BASE_DIR)
    os.chdir(BASE_DIR)   # 把目录切换到当前项目目录！！！！
    # print(os.getcwd())   # 再次打印当前项目目录：f:\cloud\code\python\quant\py_quant\src
    return os.getcwd()


# chdir_to_cur()
# print("Goodbye, World!")
# print(1+2)


def get_logger(filename: str = __file__, level=logging.DEBUG):
    root_name = 'src' if __name__ == '__main__' else __name__.split('.')[0]  # 找到项目根目录
    filename = filename[filename.rfind(root_name):]  # 通过路径找到项目根目录
    arr = re.split(r'[\\/.]', filename)
    log_name = ".".join(arr[0:-1])
    logger = logging.getLogger(log_name)
    logger.setLevel(level)  # 默认是 WARNING，会导致下面都不输出，所以要设置！！！
    log_fmt = logging.Formatter(LOG_STYLE)
    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(log_fmt)
    logger.addHandler(sh)  # 控制台同时输出！
    logging.basicConfig(force=True, filename=arr[-2] + '.log', level=level, format=LOG_STYLE, encoding="UTF-8")
    # fh = logging.FileHandler(filename=arr[-2] + '.log', encoding="UTF-8")
    # fh.setLevel(level)
    # fh.setFormatter(log_fmt)
    # logger.addHandler(fh)
    global log
    log = logger
    return logger


log = get_logger(__file__)


def println(args: list):
    for arg in args:
        print(arg)


def get_encoding(fpath=None, stream=None):
    """
    2个参数必须传一个！\n
    pip install filemagic python-magic-bin \n
    import magic
    :param fpath:
    :param stream: 文件流
    :return:
    """
    assert fpath is not None or stream is not None, "2个参数不能同时为空！"
    if fpath is None:
        encoding_dict = chardet.detect(stream)
    else:
        with open(fpath, 'rb') as file:
            file_stream = file.read()
            encoding_dict = chardet.detect(file_stream)
            # byte_array = array.array('B', file_stream)  # 变成字节数组
            # byte_string = bytes(byte_array)
            # encoding_dict = chardet.detect(byte_string)
    log.info(f"{fpath} 文件编码={encoding_dict}")
    return encoding_dict['encoding'] if encoding_dict is not None else 'utf-8'


# 未测试！
def get_filetype(fpath=None, stream=None):
    """
    2个参数必须传一个！\n
    pip install filemagic python-magic-bin \n
    import magic
    :param fpath:
    :param stream: 文件流
    :return:
    """
    assert fpath is not None or stream is not None, "2个参数不能同时为空！"
    # magic是读取文件类型！
    # print(magic.__version__)
    m = magic.Magic(mime_encoding=True)
    ftype = m.from_file(fpath) if stream is None else m.from_buffer(stream.read())
    # 以下是老版本的写法
    # with magic.Magic(flags=magic.MAGIC_MIME_ENCODING) as m:
    #     encoding = m.id_filename(fpath) if stream is None else m.id_buffer(stream.read())
    log.info(f"{fpath} 文件类型={ftype}")
    return ftype


def is_inst(obj, obj_type) -> bool:  # 判断非None类型
    return obj_type is not None and isinstance(obj, obj_type)


def is_obj(obj) -> bool:  # 判断非None的对象
    return obj is not None and is_inst(obj, object)


def not_obj(obj) -> bool:  # 判断为None或者非对象
    return not is_inst(obj, object)


def not_none(obj) -> bool:
    return obj is not None


def not_empty(obj) -> bool:  # 适用于对象、字符串、数组等
    return not is_empty(obj)


def is_empty(obj) -> bool:  # 适用于对象、字符串、数组等
    return obj is None or get_len(obj) == 0


def get_len(obj) -> int:
    return len(obj) if is_array(obj) or is_dict(obj) or isinstance(obj, str) else 0


def is_dict(obj) -> bool:
    return isinstance(obj, Mapping)


def is_set(obj) -> bool:
    return isinstance(obj, AbcSet)


def is_array(obj) -> bool:
    """
    isinstance(param, (list, tuple, set, frozenset))不够，因为其它的三方包不一定继承这个！\n
    print(util.is_array(a), util.is_array(()), util.is_array({}), util.is_array({}.items())) \n
    print(util.is_array(np.arange(1,2,3))) 以上都是true，所以不能用 Iterable！ \n
    Iterable（可迭代）：Iterable 是指实现了 __iter__() 方法的对象，可以通过迭代器进行遍历。 \n
    它是更宽泛的概念，包括了能够被遍历的对象，比如列表、元组、集合、字典等。可以使用 iter() 函数将可迭代对象转换为迭代器，然后使用 next() 函数逐个获取其中的元素。 \n
    Collection（可集合）：Collection 是指实现了 __contains__() 方法的对象，可以通过 in 或 not in 运算符来检查元素是否存在。 \n
    它是 Iterable 的子集，仅包括能够判断元素成员资格的对象。除了包含可迭代对象的特性外，还要求对象具有确定的大小（即长度是可知的）。 \n
    综上所述，所有的 Collection 都是 Iterable，但并非所有的 Iterable 都是 Collection。 \n
    例如，字符串是可迭代的，但不是可集合的，因为它没有实现 __contains__() 方法，只能 find。
    :param obj:
    :return:
    """
    return isinstance(obj, Collection) and not is_dict(obj)


def get_idx(arr, idx: int, def_val=None):  # 注意，这里只是为了不报错！
    size = get_len(arr)
    if size == 0 or size <= idx:
        return def_val
    idx = idx if idx >= 0 else (idx + size)
    if is_set(arr):
        for i, e in enumerate(arr):
            if i == idx:
                return e
    else:
        return arr[idx] if is_array(arr) else def_val


def trim_all(pars: str):
    return pars.strip().replace(' ', '')


def get_url_last(url: str, rstrip: str = None):
    last_url = url.split('/')[-1]
    return last_url if last_url is None else last_url.rstrip(rstrip)


def get_suffix(name: str) -> str:
    return split_suffix(name)[1]


def split_suffix(name: str) -> (str, str):
    """
    如果没有后缀，则返回自身全部
    :param name:
    :return: file_path, suffix
    """
    if is_empty(name):
        return '', ''
    idx = name.rfind(".")
    return name[0:idx], name[idx + 1:]


def split_dir(name: str) -> (str, str):
    """
    按当前目录分割
    :param name:
    :return: dir_path, file_name
    """
    if is_empty(name):
        return '', ''
    idx1 = name.rfind("/")
    idx2 = name.rfind("\\")
    idx = max(idx1, idx2)
    return name[0:idx], name[idx + 1:]


def split_dir_add(name: str, son_dir: str, suffix: str = None) -> str:
    """
    当前目录下新增子目录，方便存文件
    :param name:
    :param son_dir:
    :param suffix:
    :return:
    """
    dir_name, file_name = split_dir(name)
    if suffix is not None:
        file_name = split_suffix(file_name)[0] + suffix
    return dir_name + '/' + son_dir.strip("/\\") + "/" + file_name


def ensure_dir_exists(file_path: str):
    dir_path = file_path if os.path.isdir(file_path) else split_dir(file_path)[0]
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def file_to_base64_str(file_path) -> str:
    return file_to_base64(file_path).decode("utf-8")


def file_to_base64(file_path) -> bytes:
    with open(file_path, "rb") as file_ctx:
        file_data = file_ctx.read()
        base64_bytes = base64.b64encode(file_data)  # 二进制的字节数组
        return base64_bytes


def list_file_paths(show_path: str, file_type=None) -> list:
    """
    列出当前目录文件，不包括子目录、文件夹
    :param show_path:
    :param file_type:
    :return:
    """
    if file_type is None:
        file_paths = [show_path + i for i in os.listdir(show_path) if os.path.isfile(os.path.join(show_path, i))]
    else:
        file_paths = glob.glob(os.path.join(show_path, '*.' + file_type))
    return file_paths


@overload
def rgb_hex(rgb_r: str, rgb_g: str, rgb_b: str) -> str:
    ...


@overload
def rgb_hex(rgb_arr: tuple[int, int, int]) -> str:
    ...


def rgb_hex(*args) -> str:
    if len(args) == 3 and all(isinstance(arg, int) for arg in args):
        # print("3个参数", args)
        rgb_r, rgb_g, rgb_b = args
    elif len(args) == 1 and isinstance(args[0], tuple):
        # print("1个参数", args)
        rgb_r, rgb_g, rgb_b = args[0]
    else:
        raise TypeError("Invalid arguments for rgb_hex")
    return f"{rgb_r:02x}{rgb_g:02x}" + "{0:02x}".format(rgb_b)  # hex(rgb_b)[2:] 可以去除前缀"0x"，但没法补0


def to_list(arr) -> list:
    ret = []
    for x in arr:
        ret.append(x)
    return ret


def contain_any(lst, *elem) -> bool:
    """
    判断是否包含
    :param lst: 列表或元组等
    :param elem:
    :return:
    """
    for k in elem:
        if k in lst:
            return True
    return False


def contain_any_no_case(lst, *elem) -> bool:
    """
    判断是否包含，大小写不敏感
    :param lst: 列表或元组等
    :param elem:
    :return:
    """
    for k in elem:
        if contain_any(lst, k, k.upper(), k.lower()):
            return True
    return False


def rename_prefix(path: str, prefix: str):
    rename(path, prefix, "")


def rename_suffix(path: str, suffix: str):
    rename(path, "", suffix)


def rename(path: str, prefix: str, suffix: str):
    for file_name in os.listdir(path):
        # 获取文件完整路径
        old_file_path = os.path.join(path, file_name)
        # 重命名文件
        new_file_path = os.path.join(path, prefix + file_name + suffix)
        os.rename(old_file_path, new_file_path)
        # print(file_name, old_file_path, new_file_path)


def profile_func(func, *value):
    profiler = Profiler()
    profiler.start()
    ret = func(*value)  # 要分析的函数
    # print(ret)
    profiler.stop()
    profiler.print()


def profile_funcs(funcs: list, values: list):
    profiler = Profiler()
    profiler.start()
    for i, func in enumerate(funcs, start=0):
        func(values[i])
    profiler.stop()
    profiler.print()


def profile(func):
    """
    打印方法（包含嵌套内的方法）耗时
    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        profiler = Profiler()
        profiler.start()
        ret = func(*args, **kwargs)
        profiler.stop()
        profiler.print()
        return ret

    return wrapper


def call_log(func):
    """
    记录方法耗时和参数
    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        startTime = time.time()
        ret = func(*args, **kwargs)
        endTime = time.time()
        str_args = op(args, indent=2, enable=False)
        str_kwargs = op(kwargs, enable=False)
        str_ret = op(ret, format="json", indent=2, enable=False)
        # print(f'--- {func.__name__} 方法耗时={endTime - startTime:.3f}s,请求参数={str_args} {str_kwargs},返回参数={str_ret} ---')
        log.info(f'--- {func.__name__} 方法耗时={endTime - startTime:.3f}s,请求参数={str_args} {str_kwargs},返回参数={str_ret} ---')
        return ret

    return wrapper


def copy_arr(arr_to: list, i, arr_from):
    """
    复制到 arr_to，从第i个放置！！
    :param arr_to:
    :param i:
    :param arr_from:
    :return:
    """
    for idx, e in enumerate(arr_from):
        idx_new = i + idx
        if len(arr_to) > idx_new:
            arr_to[idx_new] = e
        else:
            arr_to.append(e)
    return arr_to


def append_arr(arr_to: list, arr_from: list[list]):
    for ee in arr_from:
        arr_to.extend(ee)
    return arr_to


def sort_by(arr_src, sort_key, arr_sort) -> list:
    temp_dict = {}
    for e in arr_src:
        sk = e[sort_key]
        if sk in temp_dict:
            temp_dict[sk].append(e)  # 此处不能用 extend，因为 dict只会被取出key ！！！
        else:
            temp_dict[sk] = [e]
    arr_ret = []
    if isinstance(arr_sort, dict):
        # append_arr(arr_ret, [temp_dict.pop(k) for k, v in arr_sort.items() if k in temp_dict])
        aa = [x for x in [temp_dict.pop(k) for k, v in arr_sort.items() if k in temp_dict]]
        print(aa, 'aa')
        arr_ret.extend([x for x in [temp_dict.pop(k) for k, v in arr_sort.items() if k in temp_dict]])
        # arr_ret.append([x for x in [temp_dict.pop(k) for k, v in arr_sort.items() if k in temp_dict]]) # 这里结果是[[]]
        # for k, v in arr_sort.items():  # 简化写法
        #     if k not in temp_dict:
        #         continue
        #     arr_ret.extend(temp_dict.pop(k))
    else:
        append_arr(arr_ret, [temp_dict.pop(k) for k in arr_sort if k in temp_dict])
    # print(arr_ret)
    for k, v in temp_dict.items():
        arr_ret.extend(v)
    return arr_ret


def get_arg(arg_name: str, arg_type, *args, **kwargs):
    """
    注意：使用时一定要打散，不然都会被args包括，如下：\n
    util.get_arg('engine', Engine, *args, **kwargs)
    :param arg_name:
    :param arg_type:
    :param args:
    :param kwargs:
    :return:
    """
    arr_type, arr_name, ret = [], [], None
    # log.info(f"{arg_name},{arg_type},args={args},kwargs={kwargs}")
    for k, v in kwargs.items():
        if arg_name == k:  # 按名称匹配关键字参数
            arr_name.append(v)
            if is_inst(v, arg_type):
                return v
        elif is_inst(v, arg_type):  # 按类型匹配参数
            arr_type.append(v)

    for a in args:  # 按类型匹配参数
        if is_inst(a, arg_type):
            arr_type.append(a)

    if not_none(arg_type) and not_empty(arr_type):
        ret = arr_type[0]
    elif not_empty(arg_name) and not_empty(arr_name):
        ret = arr_name[0]
    return ret


def copy_obj(src_obj, dest_clazz, attr_dict: dict = None, last_exec=None):
    """
    深拷贝，注意剔除非类字段，比如查询数据库的结果会自带 _sa_instance_state 等字段 \n
    所以不能简单直接用 dest_clazz(**copy.deepcopy(src_obj.__dict__))  \n
    下面这样也不行，因为不同类的构造函数不一样，可能有多个参数！！  \n
    dest_obj = dest_clazz(**{k: v for k, v in copy.deepcopy(src_obj.__dict__).items() if hasattr(dest_clazz, k)})
    :param src_obj:
    :param dest_clazz:
    :param attr_dict: 复制后设置指定属性字段
    :param last_exec: 最后执行方法
    :return:
    """
    # 获取目标类的构造函数
    init_func = inspect.signature(dest_clazz)
    init_pars = [None for k, v in init_func.parameters.items()]
    dest_obj = dest_clazz(*init_pars)
    for attr, value in src_obj.__dict__.items():
        if hasattr(dest_clazz, attr):
            setattr(dest_obj, attr, copy.deepcopy(value))
    set_arr(dest_obj, attr_dict)
    if last_exec is not None:
        last_exec(dest_obj)
    return dest_obj


def set_arr(obj, attr_dict: dict):
    if attr_dict is None:
        return obj
    for k, v in attr_dict.items():
        # obj.__dict__[k] = v  # 这样都不是新增字段！
        setattr(obj, k, v)
    return obj


def now_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return time_str(time.localtime(), fmt)


def time_str(dtime: time, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return time.strftime(fmt, dtime)


def replace_idx(text: str, old, new, start_idx: int):
    prefix = text[:start_idx]
    suffix = text[start_idx:]
    replaced_suffix = suffix.replace(str(old), str(new))
    return prefix + replaced_suffix


if __name__ == '__main__':
    print(get_suffix("aaa"))
    print(list_file_paths("E:\\img\\human"))
    rgb = 11, 11, 11
    print(rgb_hex(rgb))
    print(rgb_hex(*rgb))
    print(rgb_hex(11, 11, 11))
    print(split_dir('E:\cloud\code\python\quant\py_quant\src\\fun/img_background.py'))
    print('/\\sss\\/'.strip('\\/'))
    print('/sss/\\'.strip('/\\'))
    print(file_to_base64('E:\\cloud\\code\\python\\quant\\py_quant\\src\\fun\\img_background.py'))
    ensure_dir_exists('e:/img/result_out/j_custom.png')
    print(split_dir_add('E:/img/yy.jpg', 'result_out', '_blue.png'))
    arr = [1, 2, 3, 4]
    print(arr[::-1])
    arr.reverse()
    print(arr)
    print(copy_arr([0, 1], 1, [1, 2, 3]), '-----')
    arr.extend([1, 2, 3])
    print(arr)
    ds = [{'a', 1}, {'b': 2}]
    ds.extend([{'a', 1}, {'b': 2}])
    print(ds, '--- extend ---')
    ds.extend(*[[{'a', 1}, {'b': 2}]])  # 可以直接打散！！！！
    print(ds, '--- extend [] ---')
    print(sort_by([{'aa': 'SZ002176'}, {'aa': 'SH600397'}, {'aa': 'SZ002176'}, {'aa': '1SZ002176'}], 'aa', ('SZ002176','SH600397')))
    print(sort_by([{'aa': 'SZ002176'}, {'aa': 'SH600397'}, {'aa': 'SZ002176'}, {'aa': '1SZ002176'}], 'aa', {'SZ002176': '江特电机', 'SH600397': '安源煤业', 'SH600792': '云煤能源', 'SH605011': '杭州热电'}))
