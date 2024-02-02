import functools
import logging
import os
import re
import threading
from concurrent import futures
import utils.common_util as util

RSP_LINE = lambda le: le.rstrip('\r\n')
# LOG_STYLE = '%(asctime)s [%(threadName)s] [%(levelname)s] %(filename)s %(funcName)s:%(lineno)d %(message)s'
log = None


# def get_logger(filename: str = __file__, level=logging.DEBUG):
#     root_name = 'src' if __name__ == '__main__' else __name__.split('.')[0]  # 找到项目根目录
#     filename = filename[filename.rfind(root_name):]  # 通过路径找到项目根目录
#     arr = re.split(r'[\\/.]', filename)
#     log_name = ".".join(arr[0:-1])
#     logger = logging.getLogger(log_name)
#     logger.setLevel(level)  # 默认是 WARNING，会导致下面都不输出，所以要设置！！！
#     log_fmt = logging.Formatter(LOG_STYLE)
#     sh = logging.StreamHandler()
#     sh.setLevel(level)
#     sh.setFormatter(log_fmt)
#     logger.addHandler(sh)  # 控制台同时输出！
#     logging.basicConfig(force=True, filename=arr[-2] + '.log', level=level, format=LOG_STYLE, encoding="UTF-8")
#     # fh = logging.FileHandler(filename=arr[-2] + '.log', encoding="UTF-8")
#     # fh.setLevel(level)
#     # fh.setFormatter(log_fmt)
#     # logger.addHandler(fh)
#     global log
#     log = logger
#     return logger


def get_cur_filename(fpath: str = __file__, strip_suffix: bool = None, rep_suffix: str = None) -> str:
    """
    获取当前文件名（类似参数 __name__ = src.utils.file_util）
    :param fpath: 注意，这个一定要传参 __file__，不能在该方法内直接写死，否则就永远是该方法的文件名！！
    :param strip_suffix:
    :param rep_suffix:
    :return:
    """
    cur_file = os.path.basename(fpath)  # 获取当前文件名
    if strip_suffix:  # 去除后缀，将文件名分割成文件名和扩展名两部分返回一个元组
        cur_file = os.path.splitext(cur_file)[0]
    if rep_suffix:
        cur_file += rep_suffix
    return cur_file


def chdir_to_cur(fpath: str = __file__):
    # print("    该文件路径：", ) # 该文件路径： f:\cloud\code\python\quant\py_quant\src\hello-world.py
    # print("该文件绝对路径：", os.path.abspath(filePath)) # 该文件路径： f:\cloud\code\python\quant\py_quant\src\hello-world.py
    # print("  当前项目地址：", os.getcwd()) # 当前项目目录： F:\cloud\code\python\quant\py_quant
    BASE_DIR = os.path.dirname(os.path.abspath(fpath))  # 这里保险的就是直接先把绝对路径加入到搜索路径
    # print("    该文件目录：", BASE_DIR)
    os.chdir(BASE_DIR)   # 把目录切换到当前项目目录！！！！
    # print(os.getcwd())   # 再次打印当前项目目录：f:\cloud\code\python\quant\py_quant\src
    return os.getcwd()


def run_with_map(pool: futures.ThreadPoolExecutor, lines, line_action, action, par_dict: dict) -> (bool, str):
    func = functools.partial(action, **par_dict)  # 不指定则默认为第一个，然后依次
    # results = pool.map(func, lines)
    results = pool.map(lambda le: func(line_action(le)), lines)  # 每个都处理一下
    for result, line in zip(results, lines):
        if result:
            pool.shutdown(wait=False, cancel_futures=True)
            line = line_action(line)  # line.rstrip('\r\n')
            log.info(f"执行成功：line={line},result={result}")
            return True, line
    # 可以不写，但不要写 False,  这样下面获取返回的时候可能出问题！！！
    return False, None


def run_chunk_with_map(fpath: str, chunk_size: int, line_action, action, par_dict: dict, thread_num=5, last_act=None) -> str:
    """
    文件块执行最好！！！
    :param fpath: 文件路径
    :param chunk_size: 单位 KB
    :param line_action: 行数据处理，一般是 RSP_LINE = lambda le: le.rstrip('\r\n')，不处理则传 lambda x: x
    :param action: 利用线程池处理整块·多行数据
    :param par_dict: action执行参数
    :param thread_num:
    :param last_act: 执行完成后，处理结果
    :return:
    """
    ret_line = ''  # 用于保存 run_with_map 的返回值

    def run_callback(lines):
        nonlocal ret_line  # 使用 nonlocal 关键字声明 result 为外部函数变量
        res, line = run_with_map(pool, lines, line_action, action, par_dict)
        if res:
            ret_line = line
            return res  # 一定要加，否则即使找到，线程也停不住！！

    with futures.ThreadPoolExecutor(max_workers=thread_num, thread_name_prefix='pool-chunk') as pool:
        # read_chunk(fpath, chunk_size, lambda lines: run_with_map(pool, lines, line_action, action, par_dict))
        read_chunk(fpath, chunk_size, run_callback)
    if last_act:
        last_act(last_act)
    return ret_line


def read_chunk(fpath: str, chunk_size: int, process_lines, encode='utf-8'):
    """
    文件按块读取处理。通常情况下，整块解码 (decode('utf-8')) 比逐行解码更快。这是因为整块解码可以利用底层的优化算法和操作系统级别的缓存来提高解码速度。
    逐行解码需要对每一行都进行解码操作，这可能会导致频繁的解码调用，增加了额外的开销。而整块解码只需要一次解码操作，然后对整个块的文本进行处理，从而减少了解码的次数。
    此外，整块解码还可以利用并行处理的优势，因为它可以在一个线程中进行解码操作，而不需要等待每一行的解码完成。
    当然内存占用也会增大，但这已经是按块执行，所以正好！
    :param fpath:
    :param chunk_size: 字节大小byte，一般是1024B=1KB的倍数，实际使用为了方便，此处单位为 KB ！
    :param process_lines: 处理多行函数，返回值为bool，方便结束块循环
    :param encode:
    :return:
    """
    with open(fpath, 'rb') as file:
        last_line, i = b'', 1
        while True:
            chunk = file.read(chunk_size << 10)  # 位运算不支持浮点数，read也是必须要整型
            chunk_len = len(chunk)
            bk_size, bk_unit = (chunk_len >> 10, 'KB') if chunk_len >= 1024 else (chunk_len, 'B')
            log.info(f"--- 读取第{i}块，大小={bk_size}{bk_unit} ---")
            i += 1
            if not chunk:
                log.info('--- 文件块读取结束！ ---')
                break
            chunk = last_line + chunk  # 将上一个块的最后一行与当前块的第一行拼接起来
            idx = chunk.rfind(b'\n')
            if idx != -1:
                lines = chunk[:idx].decode(encode).split('\n')
                log.info(f"文件块[0, {len(lines)})={RSP_LINE(lines[0])} ...... {RSP_LINE(lines[-1])}")
                last_line = chunk[idx + 1:]
                if process_lines(lines):
                    log.info('--------- 处理成功退出！ ------')
                    return
            else:
                lines, last_line = [], chunk
        # 处理最后一个不完整的行
        if last_line and process_lines([last_line.decode(encode)]):
            log.info('--------- 处理最后一份文件块 ------')
            return


def read_chunk_line(fpath: str, chunk_size: int, process_line, encode='utf-8'):
    """
    文件按块读取处理，该方法已废弃！！！
    :param fpath:
    :param chunk_size: 字节大小byte，一般是1024B=1KB的倍数，实际使用为了方便，此处单位为 KB ！
    :param process_line: 处理单行函数
    :param encode:
    :return:
    """
    with open(fpath, 'rb') as file:
        last_line = b''
        while True:
            chunk = file.read(chunk_size << 10)
            if not chunk:
                break
            # 将上一个块的最后一行与当前块的第一行拼接起来
            lines = (last_line + chunk).split(b'\n')
            last_line = lines[-1]
            for line in lines[:-1]:
                process_line(line.decode(encode))  # 对每个完整的行进行处理
        # 处理最后一个不完整的行
        if last_line:
            process_line(last_line.decode(encode))


def clear(fpath, title: str = None):
    with open(fpath, "w", encoding='utf-8') as file:
        file.truncate(0)
        if title is not None:
            file.write(title + '\n\n')  # writelines 不会自动换行，只是接受参数是list


def read_props(fpath: str, **kwargs) -> dict:
    properties = {}
    encoding = util.get_encoding(fpath)
    with open(fpath, 'r', encoding=encoding) as file:
        for line in file:
            line = line.strip()
            if not util.is_empty(line) and not line.startswith('#'):
                key, value = line.split('=', 1)
                properties[key.strip()] = value.strip()
    if kwargs:  # 更新覆盖，不存在则在最后新增
        properties.update(kwargs)
    return properties


def cover_props(fpath: str, **kwargs):
    if kwargs is None:  # 不能全部清空，避免误操作！
        return
    encoding = util.get_encoding(fpath)
    lines = []
    with open(fpath, 'r', encoding='utf-8') as file:
        for line in file:
            line_str = line.strip()
            if not util.is_empty(line_str) and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                if key in kwargs:
                    val_new = kwargs[key]
                    idx = line.find('=')
                    line = util.replace_idx(line, value.strip(), val_new, idx)
            lines.append(line)

    with open(fpath, 'w', encoding=encoding) as file:
        file.writelines(lines)


if __name__ == '__main__':
    log = util.get_logger()
    file_path = 'C:/Users/jiangpq/Desktop/nginx.conf'
    # read_block(file_path, 1, lambda e:  e)  # lambda不处理
    # read_chunk_line(file_path, 1, print)
    # read_chunk(file_path, 1, lambda lines: [print(e) for e in lines])
    # print(read_props('E:/cloud/code/python/PiPiName/config.py'))
    print(cover_props('E:/cloud/code/python/PiPiName/config.py', last_name='"陶"'))
