from enum import Enum


class DataType(Enum):
    DEF = (0, '默认现成库')
    SHI_JING = (1, '诗经')
    CHU_CI = (2, '楚辞')
    LUN_YU = (3, '论语')
    ZHOU_YI = (4, '周易')
    TANG_SHI = (5, '唐诗')
    SONG_CI = (6, '宋词')

    def __init__(self, key, display: str):
        self.key = key
        self.display = display
