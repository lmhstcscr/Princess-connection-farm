import time

import psutil

from core.MoveRecord import moveerr
from core.cv import UIMatcher
from core.log_handler import pcr_log
from pcr_config import bad_connecting_time, async_screenshot_freq
from ._base import BaseMixin

screenshot = None
th_sw = 0


class AsyncMixin(BaseMixin):
    """
    异步插片
    包含异步函数
    """

    async def juqingtiaoguo(self):
        # 异步跳过教程 By：CyiceK
        # 测试
        global th_sw
        global screenshot
        while th_sw == 0:
            cpu_occupy = psutil.cpu_percent(interval=5, percpu=False)
            if screenshot is None:
                time.sleep(0.8)
                continue
            if cpu_occupy >= 80:
                # print('ka')
                time.sleep(0.8)
            try:
                # await asyncio.sleep(10)
                # time.sleep(10)
                # 过快可能会卡
                if UIMatcher.img_where(screenshot, 'img/caidan_yuan.jpg', at=(860, 0, 960, 100)):
                    self.click(917, 39)  # 菜单
                    time.sleep(1)
                    self.click(807, 44)  # 跳过
                    time.sleep(1)
                    self.click(589, 367)  # 跳过ok
                    time.sleep(5)
                if UIMatcher.img_where(screenshot, 'img/kekeluo.bmp', at=(181, 388, 384, 451)):
                    # 防妈骑脸
                    self.click(1, 1)
                    time.sleep(3)
                    self.click(1, 1)
                if UIMatcher.img_where(screenshot, 'img/dxc_tb_1.bmp', at=(0, 390, 147, 537)):
                    self.lockimg('img/liwu.bmp', elseclick=[(131, 533)], elsedelay=1)  # 回首页
                if UIMatcher.img_where(screenshot, 'img/dxc_tb_2.bmp', at=(580, 320, 649, 468)):
                    time.sleep(4)
                    self.click(610, 431)
                    self.lockimg('img/liwu.bmp', elseclick=[(131, 533)], elsedelay=1)  # 回首页

            except Exception as e:
                pcr_log(self.account).write_log(level='error', message='异步线程终止并检测出异常{}'.format(e))
                th_sw = 1
                # sys.exit()
                break

    async def bad_connecting(self):
        # 异步判断异常 By：CyiceK
        # 测试
        _time = 0
        global th_sw
        global screenshot
        while th_sw == 0:
            if screenshot is None:
                time.sleep(0.8)
                continue
            cpu_occupy = psutil.cpu_percent(interval=5, percpu=False)
            if cpu_occupy >= 80:
                # print('ka')
                time.sleep(0.8)
            try:
                time.sleep(bad_connecting_time)
                # 过快可能会卡
                time_start = time.time()
                if UIMatcher.img_where(screenshot, 'img/connecting.bmp', at=(748, 20, 931, 53)):
                    # 卡连接
                    time.sleep(1)
                    time_end = time.time()
                    _time = time_end - time_start
                    _time = _time + _time
                    if _time > bad_connecting_time:
                        _time = 0
                        # LOG().Account_bad_connecting(self.account)
                        raise moveerr("reboot", "connecting时间过长")
                if UIMatcher.img_where(screenshot, 'img/loading.bmp', threshold=0.8):
                    # 卡加载
                    # 不知道为什么，at 无法在这里使用
                    time.sleep(1)
                    time_end = time.time()
                    _time = time_end - time_start
                    _time = _time + _time
                    if _time > bad_connecting_time:
                        # LOG().Account_bad_connecting(self.account)
                        _time = 0
                        raise moveerr("reboot", "loading时间过长")

                if UIMatcher.img_where(screenshot, 'img/fanhuibiaoti.bmp', at=(377, 346, 581, 395)):
                    # 返回标题
                    raise moveerr("reboot", "网络错误，返回标题。")

                if UIMatcher.img_where(screenshot, 'img/shujucuowu.bmp', at=(407, 132, 559, 297)):
                    # 数据错误
                    raise moveerr("reboot", "数据错误，返回标题。")

            except moveerr as e:
                pcr_log(self.account).write_log(level="error", message=f"异步线程检测出PCR异常：{e.desc}")
                raise e
            except Exception as e:
                if type(e) is moveerr:
                    # 向主线程传递错误
                    raise e
                else:
                    pcr_log(self.account).write_log(level='error', message='异步线程终止并检测出异常{}'.format(e))
                    th_sw = 1

                # sys.exit()
                # break

    async def screenshot(self):
        """
        截图共享函数
        异步‘眨眼’截图
        """
        global screenshot
        while th_sw == 0:
            cpu_occupy = psutil.cpu_percent(interval=5, percpu=False)
            if cpu_occupy >= 80:
                # print('ka')
                time.sleep(async_screenshot_freq)
            time.sleep(async_screenshot_freq)
            # 如果之前已经截过图了，就不截图了
            if time.time() - self.last_screen_time > async_screenshot_freq:
                screenshot = self.getscreen()
            else:
                if self.last_screen is not None:
                    screenshot = self.last_screen
                else:
                    screenshot = self.getscreen()
            # print('截图中')
            # cv2.imwrite('test.bmp', screenshot)

    def start_th(self):
        global th_sw
        th_sw = 0

    def stop_th(self):
        global th_sw
        th_sw = 1
        self.fast_screencut_switch = 0

    def start_async(self):
        account = self.account
        self.c_async(self, account, self.screenshot(), sync=False)  # 异步眨眼截图,开异步必须有这个
        self.c_async(self, account, self.juqingtiaoguo(), sync=False)  # 异步剧情跳过
        self.c_async(self, account, self.bad_connecting(), sync=False)  # 异步异常处理

    def fix_reboot(self, back_home=True):
        # 重启逻辑：重启应用，重启异步线程
        self.stop_th()
        self.d.session("com.bilibili.priconne")
        time.sleep(8)
        self.start_th()
        self.start_async()
        if back_home:
            self.lockimg('img/liwu.bmp', elseclick=[(131, 533)], elsedelay=1)  # 回首页

    def fix_fanhuibiaoti(self):
        # 返回标题逻辑
        # 放弃不用，没有重启来的稳
        self.stop_th()
        self.guochang(screenshot, ['img/fanhuibiaoti.bmp'], suiji=0)
        time.sleep(8)
        self.start_th()
        self.start_async()
        self.lockimg('img/liwu.bmp', elseclick=[(131, 533)], elsedelay=1)  # 回首页

    def fix_shujucuowu(self):
        # 数据错误逻辑
        # 放弃不用，没有重启来的稳
        time.sleep(1)
        self.click(479, 369)
        time.sleep(8)
        self.click(1, 1)
