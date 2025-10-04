import tkinter as tk
import tkintertools as tkt # pyright: ignore[reportMissingTypeStubs]
import threading
import requests
import time
import os
import yaml

from typing import Literal, TypedDict
from collections.abc import Callable
from tkinter import messagebox

from folder import folder
from config import config, name, VersionRepository, branch
from Tools import DevThing, GetContentFromGithub
from NeoLink import CreateNeoLink
from Notice import Notice


notice = Notice()
CheckDev = DevThing("CheckDev")
AllDev = DevThing("AllDev")
# CheckDev.ChangeInDev(True)
# AllDev.ChangeInDev(True)

class VersionsDict(TypedDict):
    jar: str
    exe: str
    config: str
    env: str

# 添加缓存机制，避免频繁请求
_last_check_result = None
_last_check_time = 0
ChinaUser = False
CACHE_DURATION = 3600  # 1小时缓存

class NeoLink_kingda:
    def __init__(self, root: tk.Tk | tkt.Tk):
        self.root = root
        self.parents = tk.Frame(self.root)
        self.parents.pack()

        self.pack()

    def pack(self):
        lbl_1 = tk.Label(self.parents, text='')
        lbl_1.pack()
        
        if ChinaUser:
            lbl_1.config(text='检测到您是中国内地用户，切换到镜像网站')
        else:
            lbl_1.config(text='检测到您不是中国内地用户，切换到原始网站')
        
        self.SerialNumber = tk.Entry(self.parents)
        self.SerialNumber.pack()
        
        # 复选框
        self.DowloadLatestNeoLink = tk.Button(self.parents, text='下载最新版 NeoLink ', command=self.download_latest_NeoLink)
        self.DowloadLatestNeoLink.pack()

        self.RunBtn = tk.Button(self.parents, text='运行 NeoLink ',command=self.run)
        self.RunBtn.pack()

    def download_latest_NeoLink(self):
        # 'jar': 'NeoLinkProxy/NeoLink/releases/download/3.2/NeoLink-3.2-RELEASE.jar' # jar 文件
        # 'exe': 'NeoLinkProxy/NeoLink/releases/download/3.2/NeoLink-3.2-RELEASE.exe' # exe 文件
        # 'config': 'NeoLinkProxy/NeoLink/releases/download/3.2/config.cfg' # 配置文件
        # 'env': 'NeoLinkProxy/NeoLink/releases/download/3.2/NeoLink-3.2-env-bundled.7z' # 包含环境的文件
        versions: VersionsDict = yaml.safe_load(GetContentFromGithub(
            VersionRepository,
            branch,
            'latest.yaml',
            os.path.join(folder, 'latest.yaml'),
            ChinaUser
        ))


    def run(self):
        CreateNeoLink(
            os.path.join(folder, 'log.txt'),
            'G:\\NeoLink-3.2-env-bundled\\NeoLink-3.2-RELEASE.jar',
            5173,
            'abcd',
            os.path.join(folder, './Zulu/zulu-21/bin/java.exe')
        )

def check_china_user(callback: Callable[[bool], None] | None=None):
    """检测用户是否在中国内地（不使用异步）"""
    global _last_check_result, _last_check_time
    
    # 检查缓存
    current_time = time.time()
    if _last_check_result is not None and (current_time - _last_check_time) < CACHE_DURATION:
        CheckDev.dev_print(f"使用缓存的检测结果: {_last_check_result}")
        if callback:
            callback(_last_check_result)
        return
    
    try:
        # 使用多个备选服务提高可靠性
        services = [
            "https://ipapi.co/json/",
            "https://ipwho.is/",
            "http://www.geoplugin.net/json.gp"
        ]
        
        country = ""
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                data = response.json()
                CheckDev.dev_print(f"服务 {service} 返回数据: {data}")
                
                # 根据不同服务的返回格式提取国家代码
                if 'error' in data and data['error']:
                    continue  # 跳过有错误的服务
                
                if 'country' in data:
                    country = data['country']
                elif 'country_code' in data:
                    country = data['country_code']
                elif 'geoplugin_countryCode' in data:
                    country = data['geoplugin_countryCode']
                
                if country:
                    break  # 成功获取到国家代码就退出循环
                    
            except Exception as service_error:
                print(f"服务 {service} 请求失败: {service_error}")
                continue
        
        if not country:
            raise Exception("所有地理位置服务都不可用")
        
        # 判断是否为中国大陆地区
        is_china_user = (country.upper() in ["CN", "CHN", "CHINA"])
        CheckDev.dev_print(f"用户所在国家/地区: {country}, 是否中国内地: {is_china_user}")
        
        # 缓存结果
        _last_check_result = is_china_user
        _last_check_time = time.time()
        
        if callback:
            callback(is_china_user)
            
    except Exception as e:
        CheckDev.dev_print(f"地理位置检测失败: {e}")
        # 出现异常时使用缓存结果或默认不视为中国用户
        if _last_check_result is not None:
            result = _last_check_result
        else:
            result = False  # 默认值
            
        if callback:
            callback(result)

UseSite: Literal['https://bgithub.xyz/', 'https://github.com/'] = config["Site"]

def check_cb(is_china_user: bool):
    global UseSite, ChinaUser
    ChinaUser = is_china_user
    if is_china_user:
        UseSite = config["Mirror"]
    else:
        UseSite = config["Site"]
    AllDev.dev_print(f"{UseSite = }")



def main():
    # print('检测中\n', '正在进行检测，请稍候...', sep='    ')
    notice.EmitNotice_New('检测中', '正在进行检测，请稍候...')
    check_china_user(callback=check_cb)
    AllDev.dev_print(config)
    # threading.Thread(target=lambda: AllDev.dev_print(GetContentFromGithub(name, repository, branch, 'latest.yaml', ChinaUser))).start()

    root = tkt.Tk(title="NeoLink Kingda")
    root.config(bg="#2B2B2B")
    app = NeoLink_kingda(root=root)

    root.mainloop()

if __name__ == "__main__":
    main()
