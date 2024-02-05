import threading
import time
from tkinter import StringVar, Button, Entry, Label, LabelFrame, ttk, VERTICAL, NSEW, EW, NS, filedialog, messagebox, Tk

import opencc
from tqdm import tqdm

import config
from config import name_source, last_name, dislike_words, \
    min_stroke_count, max_stroke_count, allow_general, name_validate, gender, \
    check_name, check_name_resource
from data_type import DataType
from name_set import check_resource, get_source
from wuge import check_wuge_config, get_stroke_list, get_stroke_type
import utils.file_util as fu
import utils.common_util as util
log = util.get_logger(__file__)
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
            line += f'[{di_arr[0]}={di_arr[1]} {di_arr[2]}][{zong_arr[0]}={zong_arr[1]} {zong_arr[2]}]'
            line += f'[{wai_arr[0]}={wai_arr[1]} {wai_arr[2]}]\t{sancai_arr[0]}={sancai_arr[1]} {sancai_arr[2]}\n\n'
            f.write(line)
        print(f">>输出完毕，请查看「{file_name}」文件")


class MyGui:
    def __init__(self, init_window_name):
        self.init_window_name = init_window_name
        self.full_name = StringVar()
        self.data_src = StringVar()
        self.strokes = StringVar()
        self.tian = StringVar()
        self.di = StringVar()
        self.ren = StringVar()
        self.zong = StringVar()
        self.san_cai = StringVar()
        self.lock = threading.Lock()  # 创建线程锁
        self.stop_flag = False  # 全局停止
        self.stop_event = threading.Event()
        self.single_click_flag = False
        # 密码文件路径
        self.get_pwd_path = StringVar()  # 设置可变内容
        self.get_wifi_value = StringVar()  # 获取破解wifi账号
        self.pojie_txt = StringVar(value='开始破解')
        self.get_wifi_pwd = StringVar()  # 获取wifi密码

    def __str__(self):
        # 自动会调用的函数，返回自身的网卡
        return '(WIFI:%s,%s)' % (self.wifi, self.iface.name())

    # 设置窗口
    def set_init_window(self):
        self.init_window_name.title("姓甚名谁")
        self.init_window_name.geometry('580x600')  # width * height
        px, py, ipy = 30, 10, 0
        labelframe = LabelFrame(width=10, height=20, text="配置", pady=py)  # 设置宽高不生效，是又下面的方格自适应，可通过改 column 实现
        labelframe.grid(column=0, row=0, padx=px, pady=py)  # 框架，以下对象都是对于labelframe中添加的
        # sticky：N、S、E 和 W 分别代表了上、下、右、左对齐，NSEW显然是居中
        self.search = Button(labelframe, text="扫描WiFi", width=12, command=self.scans_wifi_list).grid(column=0, row=0)
        self.pojie = Button(labelframe, text="停止破解暂未处理好!", command=self.stop_read_pwd).grid(column=6, row=0)
        self.wifi_text = Label(labelframe, text="WiFi账号：").grid(column=0, row=2)
        self.wifi_input = Entry(labelframe, width=30, textvariable=self.get_wifi_value).grid(column=1, columnspan=3, row=2, sticky=EW)
        self.pojie = Button(labelframe, text="开始破解", command=self.try_read_pwd, textvariable=self.pojie_txt).grid(column=6, row=2)
        self.wifi_pwd_text = Label(labelframe, text="WiFi密码：").grid(column=0, row=3)
        self.wifi_pwd_input = Entry(labelframe, width=20, textvariable=self.get_wifi_pwd).grid(column=1, columnspan=2, row=3, sticky=EW)
        self.click_verify = Button(labelframe, text="验证密码", command=self.verify_pwd).grid(column=3, row=3)
        self.pwd_file = Button(labelframe, text="添加密码文件", command=self.add_pwd_file).grid(column=6, columnspan=3, row=3)
        self.label = Label(labelframe, text="目录路径：").grid(column=0, row=4)
        self.pwd_path = Entry(labelframe, width=60, textvariable=self.get_pwd_path).grid(column=1, columnspan=6, row=4, sticky=EW)
        self.wifi_labelframe = LabelFrame(width=0, height=30, pady=py-210, text="wifi列表")
        wifi_hg, wifi_lf_hg = 50, 5
        self.wifi_labelframe.grid(column=0, row=1, padx=px, pady=py, ipady=wifi_lf_hg, columnspan=4, rowspan=2, sticky=NSEW)
        # 定义树形结构与滚动条
        self.wifi_tree = ttk.Treeview(self.wifi_labelframe, show="headings", columns=("a", "b", "c", "d"))
        self.wifi_tree.grid(column=0, row=0, padx=px-10, pady=py+10, ipadx=40, ipady=wifi_hg-wifi_lf_hg, sticky=NSEW)
        self.vbar = ttk.Scrollbar(self.wifi_labelframe, orient=VERTICAL, command=self.wifi_tree.yview)
        self.vbar.grid(column=1, row=0, sticky="ns")
        self.wifi_tree.configure(yscrollcommand=self.vbar.set)
        # 表格的标题
        self.wifi_tree.column("a", width=40, anchor="center")
        self.wifi_tree.column("b", width=60, anchor="center")
        self.wifi_tree.column("c", width=160, anchor="center")
        self.wifi_tree.column("d", width=120, anchor="center")
        self.wifi_tree.heading("a", text="序号")
        self.wifi_tree.heading("b", text="信号强度")
        self.wifi_tree.heading("c", text="WIFI")
        self.wifi_tree.heading("d", text="BSSID")
        self.wifi_tree.grid(row=4, column=0, sticky=NSEW)
        '''
        <Button-1>表示鼠标左键， <Button-2>表示鼠标中键， <Button-3>表示鼠标右键，
        <Button-4>表示滚轮上滑（Linux）, <Button-5>表示滚轮下滑（Linux）
        '''
        self.wifi_tree.bind("<Double-1>", self.on_db_click)
        self.wifi_tree.bind("<Button-1>", self.on_single_click)
        self.vbar.grid(row=4, column=1, sticky=NS)

    def scans_wifi_list(self) -> list:
        self.iface.scan()
        for i in tqdm(range(3), desc='扫描可用 WiFi中'):
            time.sleep(0.5)
        log.info("扫描完成！")
        wifi_name_dict = {}  # 存放wifi名的集合
        bss = self.iface.scan_results()
        for w in bss:
            ssid = w.ssid.encode('raw_unicode_escape').decode('utf-8')  # 解决乱码问题
            signal = 100 + w.signal
            if ssid not in wifi_name_dict or signal > wifi_name_dict[ssid][0]:
                wifi_name_dict[ssid] = (signal, w.bssid)
        wifi_info_list = [(signal, name, bssid) for name, (signal, bssid) in wifi_name_dict.items()]
        # 存入列表并按信号排序，格式化输出
        wifi_info_list = sorted(wifi_info_list, key=lambda a: a[0], reverse=True)
        log.info(f"{'-' * 38}")
        log.info('{:4}{:6}{:28}{:24}'.format('编号', '信号强度', 'WIFI', 'BSSID'))
        for i, kv in enumerate(wifi_info_list):
            log.info('{:<6d}{:<6d}{:<32s}{:<20s}'.format(i, kv[0], kv[1], kv[2]))
        log.info('-' * 38)  # 38个 --------
        self.show_scans_wifi_list(wifi_info_list)
        return wifi_info_list

    # 显示wifi列表
    def show_scans_wifi_list(self, scans_res):
        self.wifi_tree.delete(*self.wifi_tree.get_children())  # 先清空
        for index, wifi_info in enumerate(scans_res):
            self.wifi_tree.insert("", 'end', values=(index + 1, wifi_info[0], wifi_info[1], wifi_info[2]))

    # 添加密码文件目录
    def add_pwd_file(self):
        filename = filedialog.askopenfilename()
        self.get_pwd_path.set(filename)

    # Treeview绑定事件
    def on_single_click(self, event):
        if self.single_click_flag:
            return
        self.single_click_flag = True
        self.wifi_tree.after(250, self.check_db_click, event)  # 利用参数和延迟区分单击和双击

    # Treeview绑定事件
    def on_db_click(self, event):
        self.single_click_flag = False
        self.get_wifi_value.set(self.get_sel_wifi_name('双击', event))

    def get_sel_wifi_name(self, evt_name, event):
        item = self.wifi_tree.selection()  # I003，就是第三行
        sel = event.widget.selection()
        wifi_info = self.wifi_tree.item(sel, "values")
        log.info(f"{evt_name} {item} 选中wifi信息：{wifi_info}")
        return wifi_info[2]

    def check_db_click(self, event):
        if self.single_click_flag:
            self.get_wifi_value.set(self.get_sel_wifi_name('单击', event))

        self.single_click_flag = False

    def verify_pwd(self):
        pwd_str, wifi_ssid = self.get_wifi_pwd.get(), self.get_wifi_value.get()
        self.dis_or_connect('', True)
        if self.try_connect(pwd_str, wifi_ssid):
            messagebox.showinfo('提示', '密码验证成功！！！')

    def stop_read_pwd(self):
        with self.lock:  # 加锁，避免多线程竞争
            self.stop_flag = not self.stop_flag
            self.pojie_txt.set("开始破解" if self.stop_flag else '暂停')

        if self.stop_flag:
            self.stop_event.set()
        else:
            self.stop_event.clear()

    # 读取密码字典，进行匹配
    def try_read_pwd(self):
        wifi_ssid, file_path = self.get_wifi_value.get(), self.get_pwd_path.get()
        self.dis_or_connect('', True)
        # t = threading.Thread(target=worker, args=(stop_event,))
        # t = threading.Thread(target=fu.run_chunk_with_map, args=(file_path, 1, fu.RSP_LINE, self.try_connect,
        #                                                          {'wifi_ssid': wifi_ssid}, 5, self.prop_msg))
        # t.start()
        fu.run_chunk_with_map(file_path, 1, fu.RSP_LINE, self.try_connect, {'wifi_ssid': wifi_ssid}, 5, self.prop_msg)

    def prop_msg(self, wifi_pwd):
        if wifi_pwd:
            self.get_wifi_pwd.set(wifi_pwd)
            messagebox.showinfo('提示', '破解成功！！！')

    @staticmethod
    def init_profile(wifi_ssid, pwd_str):
        # profile = pywifi.Profile()
        # profile.ssid, profile.key = wifi_ssid, pwd_str  # wifi名称、密码
        # profile.auth = const.AUTH_ALG_OPEN  # 网卡的开放
        # profile.akm.append(const.AKM_TYPE_WPA2PSK)  # wifi加密算法
        # profile.cipher = const.CIPHER_TYPE_CCMP  # 加密单元
        return

    # 对wifi和密码进行匹配
    def try_connect(self, pwd_str, wifi_ssid) -> bool:
        if self.stop_event.is_set():
            raise RuntimeError
        init_profile = self.init_profile(wifi_ssid, pwd_str)  # 创建wifi链接文件
        with self.lock:  # 加锁，避免多线程竞争
            is_ok = False if self.stop_flag else self.check_wifi_cfg(init_profile)
        return is_ok

    def check_wifi_cfg(self, init_profile) -> bool:
        pwd_str, wifi_ssid = init_profile.key, init_profile.ssid
        time_start = round(time.time())
        log.info(f"--- {time_start} 开始，wifi=[{wifi_ssid}]，密码=[{pwd_str}] ---")
        profiles = self.iface.network_profiles()  # 获取已保存的所有WiFi连接配置文件
        # self.iface.remove_all_network_profiles()  # 删除所有的wifi文件，会删掉以前所有的wifi配置，重输密码
        for profile in profiles:
            if profile.ssid == wifi_ssid:
                self.iface.remove_network_profile(profile)  # 删除指定WiFi配置文件
                break

        tmp_profile = self.iface.add_network_profile(init_profile)  # 设定新的链接文件
        is_ok = self.dis_or_connect(pwd_str, False, 5, tmp_profile)
        if not is_ok:
            self.dis_or_connect(pwd_str, True, 5)
        time_end = round(time.time())
        log.info(f"--- {time_end} 结束，耗时={time_end - time_start}s，pwd=[{pwd_str}]{'正确' if is_ok else '错误'}！")
        return is_ok

    def dis_or_connect(self, pwd_str, is_close=False, wait_count=5, tmp_profile=None):
        # status_arr = [const.IFACE_DISCONNECTED, const.IFACE_INACTIVE] if is_close else [const.IFACE_CONNECTED]
        status_arr = []
        if is_close:
            self.iface.disconnect()  # 断开所有链接
        else:
            self.iface.connect(tmp_profile)
        # 检查断开状态，不在范围内会报错AssertionError中断外面的循环，所以改成内循环判断
        # assert wifi_status in [const.IFACE_DISCONNECTED, const.IFACE_INACTIVE]
        while is_err := (status := self.iface.status()) not in status_arr:
            log.info(f"尝试{'断开' if is_close else '连接'}，当前状态={self.status_dict[status]},pwd=[{pwd_str}],次数={wait_count}")
            if not is_err or wait_count <= 0:
                break
            wait_count -= 1  # 8次4秒
            time.sleep(0.5)
        return not is_err


def on_select(combo_box, enum_clazz):
    selected_option = combo_box.get()
    sec_enum = next((member for member in enum_clazz if member.display == selected_option), None)
    print("Selected option:", sec_enum)
    return sec_enum


def get_full_name():
    return


def analysis_full_name(full_name: str):
    tian_arr, ren_arr, di_arr, zong_arr, wai_arr, sancai_arr = check_wuge_config(full_name, True)
    line = f'{tian_arr[0]}={tian_arr[1]} {tian_arr[2]}\n{ren_arr[0]}={ren_arr[1]} {ren_arr[2]}\n'
    line += f'{di_arr[0]}={di_arr[1]} {di_arr[2]}\n{zong_arr[0]}={zong_arr[1]} {zong_arr[2]}\n'
    line += f'{wai_arr[0]}={wai_arr[1]} {wai_arr[2]}\n\n{sancai_arr[0]}={sancai_arr[1]} {sancai_arr[2]}\n'
    messagebox.showinfo('分析结果', line)


def gui_start():
    iw_root = Tk()
    iw_root.geometry('580x600')
    label_data_src = Label(iw_root, text="数据来源:")
    label_data_src.pack(side='left', padx=5, pady=5)  # 将 label_data_src 设置为左对齐
    combo_data_src = ttk.Combobox(iw_root, values=[member.display for member in DataType])
    combo_data_src.current(0)  # 显然values不能为空，否则这句话会报错！！
    combo_data_src.bind('<<ComboboxSelected>>', lambda event, cb=combo_data_src: on_select(cb, DataType))
    combo_data_src.pack(side='left', padx=5, pady=5)
    label_full_name = Label(iw_root, text="姓名:")
    label_full_name.pack(side='left', padx=5, pady=5)
    in_full_name = Entry(iw_root, width=20, textvariable=get_full_name)
    in_full_name.pack(side='left', padx=5, pady=5)
    bt_analysis = Button(iw_root, text="分析姓名", command=lambda: analysis_full_name(in_full_name.get()))
    bt_analysis.pack(side='left', padx=5, pady=5)
    iw_root.mainloop()


if __name__ == '__main__':
    gui_start()
