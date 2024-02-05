import opencc

import config
from config import name_source, last_name, dislike_words, \
    min_stroke_count, max_stroke_count, allow_general, name_validate, gender, \
    check_name, check_name_resource
from data_type import DataType
from name_set import check_resource, get_source
from wuge import check_wuge_config, get_stroke_list, get_stroke_type
import utils.file_util as fu
# 繁体转简体
t2sConverter = opencc.OpenCC('t2s.json')


def contain_bad_word(first_name):
    if dislike_words is None:
        return False
    for word in first_name:
        if word in dislike_words:
            return True
    return False


def exec_config():
    if len(check_name) == 3:
        # 查看姓名配置
        check_wuge_config(check_name)
        if check_name_resource:
            check_resource(check_name)
        print(">>输出完毕")
    else:
        # 起名
        names = list()
        file_name = f"{last_name}_{name_source}.txt"
        with open(file_name, "w+", encoding='utf-8') as f:
            for i in get_source(name_source, name_validate, get_stroke_list(last_name, allow_general)):
                if i.stroke_number1 < min_stroke_count or i.stroke_number1 > max_stroke_count or \
                        i.stroke_number2 < min_stroke_count or i.stroke_number2 > max_stroke_count:
                    # 笔画数过滤
                    continue
                if name_validate and gender != "" and i.gender != gender and i.gender != "双" and i.gender != "未知":
                    # 性别过滤
                    continue
                if contain_bad_word(i.first_name):
                    # 不喜欢字过滤
                    continue
                names.append(i)
            print(">>输出结果...")
            names.sort()
            for i in names:
                f.write(last_name + str(i) + "\n")
            print(f">>输出完毕，请查看「{file_name}」文件")


def cover_config(xing: str, max_stroke: int = 36, min_stroke: int = 6, mid_aus: bool = True,
                 data_type: DataType = DataType.DEF, dislike_arr: list[str] = None):
    """
    覆盖 config.py，不仅要覆盖文本，还要覆盖值，因为有直接引用和加载引用的！
    :param xing:
    :param max_stroke:
    :param min_stroke:
    :param mid_aus:
    :param data_type:
    :param dislike_arr: 不喜欢的字
    :return:
    """
    config.last_name = xing
    config.max_stroke_count = max_stroke
    config.min_stroke_count = min_stroke
    config.allow_general = mid_aus
    config.name_source = data_type.key
    config.dislike_words = dislike_arr
    fu.cover_props('config.py', last_name=f'"{xing}"', max_stroke_count=max_stroke, min_stroke_count=min_stroke,
                   allow_general=mid_aus, name_source=data_type.key, dislike_words=dislike_arr)


def exec_all(xing: str, max_stroke: int = 36, min_stroke: int = 6, mid_aus: bool = True,
             data_type: DataType = DataType.DEF, dislike_arr: list[str] = None):
    """
    :param xing: 姓氏
    :param max_stroke: 最大笔画数
    :param min_stroke: 最小笔画数
    :param mid_aus: 中吉
    :param data_type: 0: "默认现成库", 1: "诗经", 2: "楚辞", 3: "论语", 4: "周易", 5: "唐诗", 6: "宋诗", 7: "宋词"
    :param dislike_arr: 不喜欢的字
    :return:
    """
    names = list()
    cover_config(xing, max_stroke, min_stroke, mid_aus, data_type)
    file_name = f"{xing}_{data_type.display}.txt"
    with open(file_name, "w+", encoding='utf-8') as f:
        for i in get_source(data_type.key, config.name_validate, get_stroke_list(xing, mid_aus)):
            if i.stroke_number1 < min_stroke or i.stroke_number1 > max_stroke or \
                    i.stroke_number2 < min_stroke or i.stroke_number2 > max_stroke:
                # 笔画数过滤
                continue
            if config.name_validate and gender != "" and i.gender != gender and i.gender != "双" and i.gender != "未知":
                # 性别过滤
                continue
            if contain_bad_word(i.first_name):
                # 不喜欢字过滤
                continue
            names.append(i)
        print(">>输出结果...")
        names.sort()
        for i in names:
            full_name = xing + i.first_name
            tian_arr, ren_arr, di_arr, zong_arr, wai_arr, sancai_arr = check_wuge_config(full_name, False)
            line = f"{xing}{t2sConverter.convert(str(i))}\n"
            line += f'[{tian_arr[0]}={tian_arr[1]} {tian_arr[2]}][{ren_arr[0]}={ren_arr[1]} {ren_arr[2]}]'
            line += f'[{tian_arr[0]}={tian_arr[1]} {tian_arr[2]}][{ren_arr[0]}={ren_arr[1]} {ren_arr[2]}]'
            line += f'[{di_arr[0]}={di_arr[1]} {di_arr[2]}][{zong_arr[0]}={zong_arr[1]} {zong_arr[2]}]'
            line += f'[{wai_arr[0]}={wai_arr[1]} {wai_arr[2]}]\t{sancai_arr[0]}={sancai_arr[1]} {sancai_arr[2]}\n\n'
            f.write(line)
        print(f">>输出完毕，请查看「{file_name}」文件")


if __name__ == '__main__':
    # exec_all('陶', data_type=DataType.SHI_JING)
    check_wuge_config('陶锦恒')
    check_wuge_config('陶弘景')
    check_wuge_config('陶弘毅')
