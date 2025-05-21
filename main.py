#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
微信自动发送群消息工具 (WeChat RPA Tool)

基于Python + PyAutoGUI + OpenCV的RPA工具，用于自动化操作微信PC版
- 自动启动/激活微信
- 搜索并进入指定群聊
- 输入/发送预设消息

技术栈:
- PyAutoGUI: 模拟键盘鼠标操作
- OpenCV: 图像识别，定位UI元素
- PyGetWindow: 管理和激活窗口
- 剪贴板: 确保中文文本输入的可靠性

作者: AI研发工作室
版本: 1.0.0
"""

import pyautogui
import time
import cv2
import numpy as np
import yaml
import os
import logging
import subprocess
import pygetwindow as gw
import argparse
import datetime
import pyperclip
import traceback

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 更改为DEBUG级别以获取更详细日志
    format="%(asctime)s [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s",  # 添加函数名和行号
    handlers=[
        logging.FileHandler("wechat_rpa.log", encoding="utf-8"), 
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# 延时设置
DELAY_SHORT = 2  # 短暂操作间隔（秒）
DELAY_LONG = 5   # 较长操作间隔（秒）

# 默认微信搜索框坐标（需手动校准）
DEFAULT_SEARCH_BOX_COORDS = (100, 100)

def load_config():
    """加载配置文件"""
    try:
        logger.debug("开始加载配置文件 config.yaml")
        with open("config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info(f"配置文件加载成功: {config}")
            
            # 验证必要的配置项
            required_keys = ['wechat_path', 'group_name', 'message']
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                logger.warning(f"配置文件缺少以下必要项: {missing_keys}")
            
            return config
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        return None

def save_config(config):
    """保存配置文件"""
    try:
        logger.debug(f"尝试保存配置到 config.yaml: {config}")
        with open("config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)
        logger.info(f"配置已成功保存")
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        return False

def get_message_content(config):
    """获取消息内容，优先从文件读取，支持变量替换"""
    message = config.get('message', '')
    message_file = config.get('message_file', '')
    
    logger.debug(f"从配置获取的消息: '{message}'")
    logger.debug(f"配置的消息文件路径: '{message_file}'")
    
    # 检查是否指定了消息文件且文件存在
    if message_file and os.path.exists(message_file):
        try:
            logger.info(f"尝试从文件读取消息: {message_file}")
            with open(message_file, 'r', encoding='utf-8') as f:
                message = f.read()
            logger.info(f"成功从文件读取消息，长度: {len(message)} 字符")
            logger.debug(f"文件消息内容: '{message}'")
        except Exception as e:
            logger.error(f"读取消息文件失败: {e}，将使用配置中的message")
            logger.debug(f"异常详情: {traceback.format_exc()}")
    else:
        if message_file:
            logger.warning(f"消息文件 '{message_file}' 不存在")
        logger.info(f"使用配置中的消息内容: '{message}'")
    
    # 变量替换
    now = datetime.datetime.now()
    variables = {
        'time': now.strftime('%H:%M:%S'),
        'date': now.strftime('%Y-%m-%d'),
        'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
        'weekday': now.strftime('%A')
    }
    
    logger.debug(f"准备替换的变量: {variables}")
    
    # 替换所有支持的变量
    original_message = message
    for var_name, var_value in variables.items():
        placeholder = '{' + var_name + '}'
        if placeholder in message:
            logger.debug(f"替换变量 {placeholder} -> '{var_value}'")
        message = message.replace(placeholder, var_value)
    
    if original_message != message:
        logger.debug(f"变量替换后的消息: '{message}'")
    
    # 确保消息不为空
    if not message.strip():
        message = "默认消息 - 请检查配置文件或消息文件"
        logger.warning(f"消息内容为空，使用默认消息: '{message}'")
    
    return message

def calibrate_search_box():
    """校准搜索框坐标"""
    logger.info("开始搜索框坐标校准...")
    print("\n==== 微信搜索框坐标校准 ====")
    print("请在5秒内将鼠标移动到微信搜索框的中心位置...")
    for i in range(5, 0, -1):
        print(f"{i}秒...", end="\r")
        time.sleep(1)
    
    # 获取当前鼠标位置
    x, y = pyautogui.position()
    logger.debug(f"检测到鼠标坐标: ({x}, {y})")
    print(f"\n检测到坐标: ({x}, {y})")
    
    # 更新配置文件
    config = load_config()
    if not config:
        logger.error("无法加载配置，将使用默认空配置")
        config = {}
    
    # 保存旧值以便日志显示变化
    old_x = config.get('search_box_x', None)
    old_y = config.get('search_box_y', None)
    
    config['search_box_x'] = x
    config['search_box_y'] = y
    
    if old_x is not None and old_y is not None:
        logger.info(f"搜索框坐标从 ({old_x}, {old_y}) 更新为 ({x}, {y})")
    else:
        logger.info(f"设置搜索框坐标为 ({x}, {y})")
    
    if save_config(config):
        print(f"✅ 搜索框坐标已更新: ({x}, {y})")
    else:
        print("❌ 搜索框坐标更新失败")
    
    return (x, y)

def get_search_box_coords(config):
    """从配置中获取搜索框坐标，如果不存在则使用默认值"""
    if 'search_box_x' in config and 'search_box_y' in config:
        coords = (config['search_box_x'], config['search_box_y'])
        logger.debug(f"从配置获取搜索框坐标: {coords}")
        return coords
    
    logger.warning(f"配置中未找到搜索框坐标，使用默认值: {DEFAULT_SEARCH_BOX_COORDS}")
    return DEFAULT_SEARCH_BOX_COORDS

def find_image_on_screen(template_paths, threshold=0.6):
    """
    在屏幕上查找指定模板图像的位置，支持多模板和多尺度匹配。
    
    此函数是UI自动化的核心组件，使用OpenCV进行模板匹配，用于：
    1. 定位微信搜索框（通过搜索图标）
    2. 识别群聊搜索结果
    
    参数:
        template_paths (list): 模板图片路径列表，按优先级排序
        threshold (float): 匹配阈值，越高要求越精确
        
    返回:
        tuple或None: 找到时返回中心点坐标(x,y)，未找到时返回None
    """
    logger.debug(f"开始屏幕图像查找，模板: {template_paths}, 阈值: {threshold}")
    screen = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
    screen_height, screen_width = screen.shape[:2]
    logger.debug(f"屏幕分辨率: {screen_width}x{screen_height}")

    for template_path in template_paths:
        if not os.path.exists(template_path):
            logger.warning(f"模板图不存在: {template_path}")
            continue

        template = cv2.imread(template_path)
        if template is None:
            logger.warning(f"无法读取模板图: {template_path}")
            continue
            
        template_height, template_width = template.shape[:2]
        logger.debug(f"模板图尺寸: {template_width}x{template_height}")
        
        # 尝试不同缩放比例以应对分辨率差异
        scales = [0.8, 0.9, 1.0, 1.1, 1.2]
        for scale in scales:
            logger.debug(f"尝试缩放比例: {scale}")
            try:
                resized = cv2.resize(template, None, fx=scale, fy=scale)
                result = cv2.matchTemplate(screen, resized, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                logger.debug(f"匹配度: {max_val}, 位置: {max_loc}, 缩放: {scale}")

                if max_val >= threshold:
                    h, w = resized.shape[:2]
                    center = (max_loc[0] + w // 2, max_loc[1] + h // 2)
                    logger.info(f"找到匹配图像: {template_path}, 位置: {center}, 匹配度: {max_val}")
                    return center
            except Exception as e:
                logger.error(f"模板匹配时发生错误: {e}")
                logger.debug(f"异常详情: {traceback.format_exc()}")

    logger.warning("未找到任何匹配模板图")
    return None

def is_wechat_running():
    """检查微信是否已运行"""
    try:
        logger.debug("检查微信是否运行...")
        wechat_windows = gw.getWindowsWithTitle("微信")
        result = len(wechat_windows) > 0
        logger.debug(f"发现微信窗口: {len(wechat_windows)} 个")
        if result:
            window_details = [(w.title, w.left, w.top, w.width, w.height) for w in wechat_windows]
            logger.debug(f"微信窗口详情: {window_details}")
        return result
    except Exception as e:
        logger.error(f"检查微信运行状态时出错: {e}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        return False

def launch_wechat(wechat_path):
    """通过路径启动微信"""
    try:
        logger.debug(f"检查微信安装路径: {wechat_path}")
        if not os.path.exists(wechat_path):
            logger.error(f"微信安装路径不存在: {wechat_path}")
            return False
            
        logger.info(f"微信启动中（通过安装路径）: {wechat_path}")
        subprocess.Popen(wechat_path)
        
        # 等待微信启动
        retry_count = 0
        max_retries = 10
        while retry_count < max_retries:
            time.sleep(DELAY_LONG)
            logger.debug(f"等待微信启动，尝试 {retry_count+1}/{max_retries}")
            if is_wechat_running():
                logger.info("微信已成功启动")
                return True
            retry_count += 1
        
        logger.error(f"微信启动超时，{max_retries}次尝试后仍未检测到微信窗口")
        return False
    except Exception as e:
        logger.error(f"启动微信时出错: {e}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        return False

def activate_wechat(config):
    """检查微信是否运行，未运行则启动，然后激活窗口"""
    try:
        # 检查微信是否已运行
        if is_wechat_running():
            logger.info("微信已在运行，尝试激活窗口...")
        else:
            logger.info("微信未运行，尝试启动微信...")
            if not launch_wechat(config['wechat_path']):
                logger.error("启动微信失败")
                return False
        
        # 尝试激活微信窗口
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                logger.debug(f"尝试激活微信窗口，第{retry_count+1}次...")
                wechat_windows = gw.getWindowsWithTitle("微信")
                if wechat_windows:
                    wechat_window = wechat_windows[0]
                    window_info = f"窗口标题: {wechat_window.title}, 位置: ({wechat_window.left}, {wechat_window.top}), 大小: {wechat_window.width}x{wechat_window.height}"
                    logger.debug(f"找到微信窗口: {window_info}")
                    
                    # 确保窗口不是最小化状态
                    if wechat_window.isMinimized:
                        logger.debug("微信窗口被最小化，正在恢复...")
                        wechat_window.restore()
                        time.sleep(DELAY_SHORT)
                    
                    wechat_window.activate()
                    time.sleep(DELAY_SHORT)
                    logger.debug("调用activate()方法激活窗口")
                    
                    # 将窗口移到前台
                    click_x = wechat_window.left + wechat_window.width // 2
                    click_y = wechat_window.top + 20
                    logger.debug(f"点击窗口标题栏坐标: ({click_x}, {click_y})")
                    pyautogui.click(click_x, click_y)
                    time.sleep(DELAY_SHORT)
                    
                    logger.info("成功激活微信窗口")
                    return True
                else:
                    logger.warning(f"无法找到微信窗口，重试 {retry_count+1}/{max_retries}")
            except Exception as e:
                logger.warning(f"激活窗口时出错，重试中: {e}")
                logger.debug(f"异常详情: {traceback.format_exc()}")
            
            retry_count += 1
            time.sleep(DELAY_SHORT)
        
        logger.error("多次尝试后仍无法激活微信窗口")
        return False
    except Exception as e:
        logger.error(f"激活微信窗口失败: {e}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        return False

def ensure_search_box_focus(config):
    """
    尝试多种方式激活微信搜索框，确保后续可以进行文本输入。
    
    采用双重策略：
    1. 优先使用图像识别定位搜索图标（更准确但可能受界面变化影响）
    2. 如识别失败，则使用校准的坐标直接点击（更可靠但可能需要重新校准）
    
    参数:
        config (dict): 包含搜索框坐标等配置信息
        
    返回:
        bool: 成功返回True
    """
    logger.info("开始定位微信搜索框...")
    # 策略1：通过图像识别查找搜索图标
    search_templates = ['png/search_icon_template.png', 'png/search_icon_backup.png']
    logger.debug(f"尝试通过模板图定位搜索框，模板: {search_templates}")
    pos = find_image_on_screen(search_templates, threshold=0.7)
    if pos:
        logger.info(f"找到搜索图标，点击坐标: {pos}")
        pyautogui.click(pos)
        time.sleep(DELAY_SHORT)
        return True

    # 策略2：使用配置中的坐标定位
    search_box_coords = get_search_box_coords(config)
    logger.info(f"未找到搜索图标，尝试使用配置的坐标点击搜索框: {search_box_coords}")
    pyautogui.click(search_box_coords)
    time.sleep(DELAY_SHORT)
    return True

def clear_search_box():
    """清除搜索框内容"""
    logger.info("清除搜索框内容...")
    try:
        logger.debug("按下Ctrl+A选择所有文本")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(DELAY_SHORT)
        
        logger.debug("按下Backspace删除选中文本")
        pyautogui.press('backspace')
        time.sleep(DELAY_SHORT)
        logger.info("搜索框内容已清除")
    except Exception as e:
        logger.error(f"清除搜索框内容时出错: {e}")
        logger.debug(f"异常详情: {traceback.format_exc()}")

def type_text_safely(text):
    """安全地输入文本，使用剪贴板方法"""
    logger.debug(f"尝试输入文本: '{text}', 长度: {len(text)}")
    
    # 尝试使用剪贴板输入
    try:
        # 保存原始剪贴板内容
        original_clipboard = pyperclip.paste()
        logger.debug("已保存原始剪贴板内容")
        
        # 将文本复制到剪贴板
        pyperclip.copy(text)
        logger.debug("已将文本复制到剪贴板")
        time.sleep(DELAY_SHORT)
        
        # 粘贴文本
        pyautogui.hotkey('ctrl', 'v')
        logger.debug("已执行粘贴操作 (Ctrl+V)")
        time.sleep(DELAY_SHORT)
        
        # 恢复原始剪贴板内容
        pyperclip.copy(original_clipboard)
        logger.debug("已恢复原始剪贴板内容")
        
        return True
    except Exception as e:
        logger.error(f"剪贴板输入失败: {e}，尝试直接输入")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        
        # 回退到直接输入
        try:
            pyautogui.write(text)
            logger.debug("已使用pyautogui.write方法输入文本")
            return True
        except Exception as e2:
            logger.error(f"直接输入也失败: {e2}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return False

def search_group_chat(group_name):
    """
    搜索指定的群聊并进入。
    
    采用混合策略：
    1. 使用剪贴板安全输入群名，确保中文字符正确
    2. 优先使用图像识别找到群聊搜索结果
    3. 如识别失败，使用键盘导航选择第一个结果
    
    参数:
        group_name (str): 要搜索的群聊名称
        
    返回:
        bool: 成功找到并进入群聊返回True，失败返回False
    """
    logger.info(f"开始搜索群聊: '{group_name}'")
    
    # 清除搜索框内容
    clear_search_box()

    # 输入群名（使用安全的文本输入方法）
    logger.info(f"正在输入群名: '{group_name}'")
    success = type_text_safely(group_name)
    if not success:
        logger.error("群名输入失败")
        return False
        
    time.sleep(DELAY_LONG)
    logger.debug("等待搜索结果显示...")

    # 模拟回车键触发搜索
    logger.info("模拟回车键确认搜索")
    pyautogui.press('enter')
    time.sleep(DELAY_LONG)
    logger.debug("已按回车键，等待搜索结果...")

    # 策略1：使用图像识别点击群聊搜索结果
    logger.info("尝试点击群聊搜索结果...")
    group_templates = ['png/group_result_template.png', 'png/group_result_backup.png']
    logger.debug(f"使用模板图查找群聊: {group_templates}")
    group_pos = find_image_on_screen(group_templates, threshold=0.5)

    if group_pos:
        logger.info(f"找到群聊匹配位置，点击坐标: {group_pos}")
        pyautogui.click(group_pos)
        time.sleep(DELAY_SHORT)
        logger.info("成功点击进入群聊")
        return True
    else:
        # 策略2：使用键盘导航选择第一个搜索结果
        logger.warning("未找到群聊模板图，尝试键盘选择")
        logger.debug("按下方向键选择第一个结果")
        pyautogui.press('down')  # 选择第一个搜索结果
        time.sleep(DELAY_SHORT)
        
        logger.debug("按下回车键确认选择")
        pyautogui.press('enter')
        time.sleep(DELAY_SHORT)
        logger.info("已通过键盘操作进入群聊")
        return True

def send_message_to_group(config):
    """主流程：激活微信，搜索群聊，发送消息"""
    GROUP_NAME = config['group_name']
    logger.debug(f"从配置获取的群名: '{GROUP_NAME}'")
    
    # 获取消息内容，支持从文件读取和变量替换
    MESSAGE = get_message_content(config)
    # 获取auto_send配置，默认为False（不自动发送）
    AUTO_SEND = config.get('auto_send', False)
    
    logger.info("========== 开始执行微信自动化任务 ==========")
    logger.info(f"目标群聊: '{GROUP_NAME}'")
    logger.info(f"自动发送模式: {'开启' if AUTO_SEND else '关闭'}")
    logger.info(f"消息长度: {len(MESSAGE)} 字符")
    logger.debug(f"消息前20个字符: '{MESSAGE[:20]}...'")

    # Step 1: 启动/激活微信
    logger.info("Step 1: 启动/激活微信")
    if not activate_wechat(config):
        logger.error("无法激活微信，任务终止")
        return False

    # Step 2: 定位并激活搜索框
    logger.info("Step 2: 定位并激活搜索框")
    if not ensure_search_box_focus(config):
        logger.error("无法激活搜索框，任务终止")
        return False

    # Step 3: 搜索群聊
    logger.info("Step 3: 搜索群聊")
    if not search_group_chat(GROUP_NAME):
        logger.error("无法找到群聊，任务终止")
        return False

    # Step 4: 输入消息
    logger.info("Step 4: 输入消息")
    logger.info(f"消息内容 (前100字符): '{MESSAGE[:100]}...'" if len(MESSAGE) > 100 else f"消息内容: '{MESSAGE}'")
    
    try:
        # 清空输入框
        logger.debug("清空消息输入框")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(DELAY_SHORT)
        pyautogui.press('backspace')
        time.sleep(DELAY_SHORT)
        
        # 确保焦点在输入框内
        logger.debug("点击确保焦点在输入框内")
        pyautogui.click()
        time.sleep(DELAY_SHORT)
        
        # 输入消息内容
        logger.info("开始输入消息内容...")
        success = type_text_safely(MESSAGE)
        if not success:
            logger.error("消息输入失败")
            return False
            
        logger.info("消息已成功输入到输入框")
    except Exception as e:
        logger.error(f"输入消息时发生错误: {e}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        return False
    
    # 根据配置决定是否自动发送
    if AUTO_SEND:
        logger.info("自动发送模式已开启，正在发送消息...")
        pyautogui.press('enter')
        logger.info("✅ 消息发送完成！")
    else:
        logger.info("已将消息输入到输入框，但未自动发送（自动发送模式已关闭）")
    
    logger.info("========== 微信自动化任务完成 ==========")
    return True

if __name__ == '__main__':
    """
    主程序入口点
    
    支持的运行模式:
    1. 标准模式: python main.py
    2. 校准模式: python main.py --calibrate
    3. 调试模式: python main.py --debug
    """
    try:
        # 记录系统信息
        import platform
        import sys
        logger.info(f"系统信息: {platform.platform()}, Python版本: {sys.version}")
        logger.info(f"屏幕分辨率: {pyautogui.size()}")
        
        # 添加命令行参数解析
        parser = argparse.ArgumentParser(description='微信自动发送群消息工具')
        parser.add_argument('--calibrate', action='store_true', help='校准微信搜索框坐标')
        parser.add_argument('--debug', action='store_true', help='启用更详细的调试日志')
        args = parser.parse_args()
        
        if args.debug:
            logger.setLevel(logging.DEBUG)
            logger.info("已启用调试模式，将显示详细日志")
        
        # 加载配置
        logger.info("加载配置文件...")
        config = load_config()
        if not config:
            logger.error("配置加载失败，程序终止")
            exit(1)
        
        # 如果是校准模式
        if args.calibrate:
            logger.info("启动校准模式")
            calibrate_search_box()
            exit(0)
        
        # 正常运行模式 - 搜索群聊并发送消息
        send_message_to_group(config)
        
    except Exception as e:
        logger.critical(f"程序执行过程中发生未捕获的异常: {e}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        print(f"程序出错: {e}")
        exit(1)