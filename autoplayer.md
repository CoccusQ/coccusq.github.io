# Python音乐播放器：AutoPlayer

## 前言

每次听音乐的时候，发现在音乐软件里很多想听的歌没有或者是要付费，而在b站上有很多好心人上传的音乐视频。

但是在b站上听音乐也有个问题，想要切歌的时候需要手动切换网页，很不方便。

于是我利用`python`的`selenium`库实现了一个能够根据给出的b站链接列表自动播放音乐的程序，支持**列表循环**、**单曲循环**、**乱序播放**。

## 工作原理

程序分为两部分：

第一部分是**自动登录脚本**，用来解决每次用播放器打开网页时需要登录b站的问题；

第二部分是**音乐播放器**，使用了两个线程，一个线程处理UI界面的交互逻辑，另一个线程处理音乐播放逻辑。

### Part 1 自动登录

通过搜集资料发现，b站的登录采用常见的`cookie`机制。

也就是说只要登录过一次，浏览器就会将登录信息存在`cookie`文件中；下次打开b站时，网站会先检测`cookie`文件中的登录信息，如果登录信息有效，b站就会正常登录。

于是，我们只需要在每次打开浏览器时将浏览器的`cookie`文件替换为准备好的包含b站登录信息的`cookie`即可。

这样就解决了每次使用脚本打开b站都会不断弹出登录提示的问题（这个登录提示太不人性化了，这是逼着游客登录啊）

于是我们有以下的实现代码（这段代码其实是以前在网上找的登录脚本，其来源由于年代久远暂时找不到了）

```python
# login.py
from selenium import webdriver
 
driver = webdriver.Edge()
driver.get('https://www.bilibili.com/')
 
'''
打开网页后直接登录
手动登录完成后在命令行内按回车，因为我用input阻塞了
等提示进程已结束，退出代码，可以看到同级目录下多出一个名为 jsoncookie.json的文件。里面存的是cookie
'''
 
driver.implicitly_wait(10)
 
input("手动登录，完成后请在命令行内按回车继续")
driver.get("https://www.bilibili.com/")
dictcookie = driver.get_cookies()
print('dictcookie:',dictcookie)
import json
jsoncookie = json.dumps(dictcookie)
print('jsoncookie:',jsoncookie)
with open('jsoncookie.json','w') as f:
    f.write(jsoncookie)
driver.close()
```

### Part 2 音乐播放器

#### 架构设计
这一部分程序采用双线程架构：
- **UI线程**：负责处理用户交互事件，通过按钮操作设置全局状态标志
- **播放线程**：执行核心播放逻辑，监控全局状态标志进行响应

这种设计避免了`selenium`操作阻塞主线程，确保界面始终响应流畅。

两个线程通过**共享全局变量**实现通信，以下是关键状态标志说明：

| 全局变量       | 作用域               | 功能描述                     |
|----------------|----------------------|------------------------------|
| `is_loop`      | 播放模式控制         | 列表循环                 |
| `is_repeat`    | 播放模式控制         | 单曲循环                 |
| `is_shuffle`   | 播放模式控制         | 随机播放                 |
| `is_next`      | 播放控制             | 切换下一曲           |
| `is_prev`      | 播放控制             | 切换上一曲           |
| `stop_thread`  | 程序生命周期控制     | 终止程序             |

#### 播放主循环详解

需要注意的是，由于b站初始设置问题，每次登录时默认**静音开播**并且**自动连播**，需要对这部分进行额外处理

```python
def play_loop():
    global i  # 当前播放索引
    while not stop_thread:
        # 播放索引边界检测
        if i >= num:
            if is_loop: i = 0  # 循环模式重置索引
            else: break        # 非循环模式结束播放
        
        # 加载视频页面
        driver.get(video_links[i])
        video = driver.find_element(By.CSS_SELECTOR, "video")
        
        # 首视频初始化操作
        if is_first_video:
            driver.execute_script("arguments[0].pause()", video)
            driver.execute_script("arguments[0].currentTime = 0;", video)
            # 音量/连续播放设置（略）
        
        # 获取视频元数据
        video_duration = driver.execute_script("return arguments[0].duration;", video)
        
        # 更新UI显示
        song_name_label.config(text=f"♫ {processed_song_name} ")
        current_time_label.config(text="00:00")
        
        # 启动视频播放
        driver.execute_script("arguments[0].play();", video)
        
        # 实时播放监控
        while True:
            if stop_thread: return  # 强制终止检测
            if driver.execute_script("return arguments[0].ended;", video):
                break  # 自然播放结束
            # 更新时间显示（略）
            
            # 强制切歌检测
            if is_next or is_prev:
                break  # 退出当前播放循环
            time.sleep(1)
        
        # 播放模式处理
        if not is_repeat:
            i += 1  # 非单曲循环时递增索引
```

#### 播放模式切换机制
通过`toggle_loop()`函数实现四种播放模式的轮换切换：

```python
def toggle_loop():
    global play_mode
    play_mode = play_mode % play_mode_num + 1
    
    # 模式对应操作
    if play_mode == 1:   # 列表循环
        is_loop = True
        loop_button.config(text="🔁")
    elif play_mode == 2: # 顺序播放
        is_loop = False
        loop_button.config(text="➡️")
    elif play_mode == 3: # 单曲循环
        is_repeat = True
        loop_button.config(text="🔂")
    elif play_mode == 4: # 随机播放
        shuffle_video()  # 执行洗牌算法
        loop_button.config(text="🔀")
```

#### 关键技术点解析
1. **Selenium网页控制**：
   - 通过`execute_script()`执行JavaScript直接操作视频元素
   - 示例：`driver.execute_script("arguments[0].play();", video)`启动播放
   - 示例：`driver.execute_script("return arguments[0].duration;", video)`获取视频时长

2. **随机播放实现**：

```python
def shuffle_video():
    global video_links, temp_list
    temp_list = video_links.copy()  # 备份原始列表
    random.shuffle(video_links)     # 生成随机序列
```
   
   使用临时列表保存原始顺序，恢复时直接`video_links = temp_list.copy()`

3. **跨线程通信**：
   - UI线程通过修改`is_next/is_prev`标志通知播放线程
   - 播放线程每次循环开始都会检查这些标志位

## 总结

这个程序最开始只有命令行界面，经过几次升级，最终实现了GUI界面操作。

完整代码如下：

```python
# AutoPlayerGUI.py
from selenium import webdriver
from selenium.webdriver.common.by import By
import tkinter as tk
from tkinter import font
import ctypes
import random
import time
import json
import re
import threading

with open('playlist.json', 'r') as f:
    video_links = json.load(f)
temp_list = []

driver = webdriver.Edge()
driver.get('https://www.bilibili.com/')
driver.delete_all_cookies()
with open('jsoncookie.json', 'r') as f:
    ListCookies = json.loads(f.read())
for cookie in ListCookies:
    driver.add_cookie({
        'domain': '.bilibili.com',
        'name': cookie['name'],
        'value': cookie['value'],
        'path': '/',
        'expires': None,
        'httponly': False,
    })
driver.get('https://www.bilibili.com/')

win = tk.Tk()
win.title("AutoPlayer")
win.attributes("-topmost", True)

#告诉操作系统使用程序自身的dpi适配
ctypes.windll.shcore.SetProcessDpiAwareness(1)
#获取屏幕的缩放因子
ScaleFactor=ctypes.windll.shcore.GetScaleFactorForDevice(0)
#设置程序缩放
win.tk.call('tk', 'scaling', ScaleFactor/75)

# 全局变量
stop_thread = False  # 标志位，用于结束线程
is_first_video = True
is_loop = True
is_repeat = False
is_shuffle = False
is_pause = False
is_next = False
is_prev = False
play_mode = 1
play_mode_num = 4 # 4种播放模式
i = 0
video_duration = 0
video = 0
num = len(video_links)

def play_loop():
    global i
    global is_first_video
    global is_pause
    global video_duration
    global video
    global is_prev
    global is_next
    
    while not stop_thread:  # 检查是否需要结束
        if i >= num:
            if is_loop:
                i = 0
            else:
                break

        driver.get(video_links[i])
        time.sleep(2)
        video = driver.find_element(By.CSS_SELECTOR, "video")
        if is_first_video:
            driver.execute_script("arguments[0].pause()", video)
            driver.execute_script("arguments[0].currentTime = 0;", video)
            volume_button = driver.find_element(By.CLASS_NAME, "bpx-player-ctrl-btn.bpx-player-ctrl-volume")
            volume_button.click()
            switch_button = driver.find_element(By.CLASS_NAME, "continuous-btn")
            switch_button.click()
            is_first_video = False
        video_duration = driver.execute_script("return arguments[0].duration;", video)
        minutes = int(video_duration // 60)
        seconds = int(video_duration % 60)
        temp_song_name = driver.find_element(By.CLASS_NAME, "tag-txt")
        pattern = re.compile(re.escape("发现《"))
        song_name = pattern.sub('', temp_song_name.text)
        pattern = re.compile(r'》')
        song_name = pattern.sub('', song_name)
        song_name = re.sub(r'[‘’]', "'", song_name)
        song_name = re.sub(r'[“”]', '"', song_name)
        driver.execute_script("arguments[0].play();", video)
        if song_name is not None:
            song_name_label.config(text=f"♫ {song_name} ")
            current_time_label.config(text="00:00")
            duration_label.config(text=f"/ {minutes:02d}:{seconds:02d}")
        while True:
            if stop_thread:
                return
            if driver.execute_script("return arguments[0].ended;", video):
                break
            current_time = driver.execute_script("return arguments[0].currentTime;", video)
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            current_time_label.config(text=f"{minutes:02d}:{seconds:02d}")
            if stop_thread:
                break  # 如果线程需要结束，则退出
            if is_next:
                is_next = False
                break
            if is_prev:
                is_prev = False
                break
            time.sleep(1)
        if not is_repeat:
            i += 1

def play_video():
    global video
    driver.execute_script("arguments[0].play();", video)

def pause_video():
    global video
    driver.execute_script("arguments[0].pause();", video)

def play_or_pause():
    global is_pause  # 声明is_pause为全局变量
    if is_pause:
        is_pause = False
        play_button.config(text="⏸️")  # 更新时间为暂停图标
        play_video()
    else:
        is_pause = True
        play_button.config(text="▶")  # 更新时间为播放图标
        pause_video()

def next_video():
    global video_duration
    global video
    global is_next 
    is_next = True
    #driver.execute_script(f"arguments[0].currentTime = {video_duration};", video)

def prev_video():
    global i
    global video
    global video_duration
    global is_prev
    i -= 2
    if i < 0 and is_loop:
        i = num - 2
    is_prev = True
    #driver.execute_script(f"arguments[0].currentTime = {video_duration};", video)

def fast_forward_video():
    global video
    global video_duration
    driver.execute_script(f"if (arguments[0].currentTime + 5 >= {video_duration}) arguments[0].currentTime = {video_duration}; else arguments[0].currentTime += 5;", video)

def fast_reverse_video():
    global video
    global video_duration
    driver.execute_script("if (arguments[0].currentTime - 5 <= 0) arguments[0].currentTime = 0; else arguments[0].currentTime -= 5;", video)

def shuffle_video():
    global video_links
    global temp_list
    temp_list = list(video_links)
    random.shuffle(video_links)

def revert_video():
    global is_shuffle
    global video_links
    global temp_list
    if is_shuffle:
        video_links = list(temp_list)
        is_shuffle = False

def toggle_loop():
    global play_mode
    global is_loop
    global is_repeat
    global is_shuffle
    
    play_mode += 1
    if play_mode > play_mode_num:
        play_mode = 1
    
    if play_mode == 1:  # 1-列表循环
        is_loop = True
        is_repeat = False
        loop_button.config(text="🔁")
        revert_video()
    elif play_mode == 2:  # 2-顺序播放
        is_loop = False
        is_repeat = False
        loop_button.config(text="➡️")
        revert_video()
    elif play_mode == 3:  # 3-单曲循环
        is_loop = False
        is_repeat = True
        loop_button.config(text="🔂")
    if play_mode == 4:  # 4-随机播放
        is_loop = True
        is_repeat = False
        is_shuffle = True
        loop_button.config(text="🔀")
        shuffle_video()

def on_closing():
    global stop_thread
    stop_thread = True  # 设置标志位为True，通知线程结束
    win.destroy()  # 销毁窗口
    driver.quit()  # 确保 WebDriver 正确关闭
    # 等待线程结束
    for thread in threading.enumerate():
        if thread != threading.current_thread():
            thread.join()


head_font = font.Font(font=("微软雅黑", 12))
time_font = font.Font(font=("微软雅黑", 8))
button_font = font.Font(font=("微软雅黑", 14))

head_frame = tk.Frame(win)
song_name_label = tk.Label(head_frame, text="♫", font=head_font)
current_time_label = tk.Label(head_frame, font=time_font)
duration_label = tk.Label(head_frame, font=time_font)

# 创建按钮
button_frame = tk.Frame(win)
prev_button = tk.Button(button_frame, text="⏮️", command=prev_video, font=button_font)
fast_reverse_button = tk.Button(button_frame, text="⏪", command=fast_reverse_video, font=button_font)
play_button = tk.Button(button_frame, text="⏸️", command=play_or_pause, font=button_font)
fast_forward_button = tk.Button(button_frame, text="⏩", command=fast_forward_video, font=button_font)
next_button = tk.Button(button_frame, text="⏭️", command=next_video, font=button_font)
loop_button = tk.Button(button_frame, text="🔁", command=toggle_loop, font=button_font)

# 布局按钮为水平
song_name_label.pack(side="left")
current_time_label.pack(side="left")
duration_label.pack(side="left")
head_frame.pack()
prev_button.pack(side=tk.LEFT)
fast_reverse_button.pack(side=tk.LEFT)
play_button.pack(side=tk.LEFT)
fast_forward_button.pack(side=tk.LEFT)
next_button.pack(side=tk.LEFT)
loop_button.pack(side=tk.LEFT)
button_frame.pack()

# 绑定关闭事件
win.protocol("WM_DELETE_WINDOW", on_closing)

# 启动播放循环线程
threading.Thread(target=play_loop).start()

win.mainloop()

if not stop_thread:
    driver.quit()
```