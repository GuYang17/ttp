#!/usr/bin/env python3
import os
import sys
import json
import time
import curses
from datetime import datetime
from pathlib import Path

# 打字练习主类
class TypingExercise:
    def __init__(self, exercise_name):
        # 初始化练习名称、文件路径和记录目录
        self.exercise_name = exercise_name
        self.exercise_file = Path(f"./exercises/{exercise_name}.txt")
        self.records_dir = Path("./records")
        self.records_dir.mkdir(exist_ok=True)
        
        # 检查练习文件是否存在
        if not self.exercise_file.exists():
            print(f"Error: Exercise file '{self.exercise_file}' not found!")
            sys.exit(1)
        
        # 读取练习文本内容
        with open(self.exercise_file, 'r', encoding='utf-8') as f:
            self.text = f.read()
            self.lines = self.text.splitlines(keepends=True)
            self.text = ''.join(self.lines)
        
        # 初始化统计数据
        self.total_chars = len(self.text)
        self.current_pos = 0
        self.correct_chars = 0
        self.wrong_chars = 0
        self.start_time = None
        self.end_time = None
        self.user_input = []
        self.colors = {}
      
        # 分页相关参数
        self.current_page = 0
        self.total_pages = 0
        self.page_line_count = 0
        self.pages = []
        self.page_indices = []

    # 主运行方法，负责界面显示和交互
    def run(self, stdscr):
        curses.curs_set(1)
        self.init_colors()
        self.start_time = time.time()
        
        # 获取终端尺寸，计算每页显示的行数
        height, width = stdscr.getmaxyx()
        self.page_line_count = max(1, height - 7)
        
        # 分页处理，将文本按页分割
        self.pages = []
        current_page = []
        current_chars = 0
        line_count = 0
        total_lines = 0
        
        for line in self.lines:
            content = line.rstrip('\n')
            lines_needed = (len(content) + width - 1) // width
            if lines_needed == 0:
                lines_needed = 1
                
            if line_count + lines_needed > self.page_line_count and line_count > 0:
                page_text = ''.join(current_page)
                self.pages.append(page_text)
                self.page_indices.append((current_chars - len(page_text), current_chars))
                current_page = [line]
                current_chars += len(line)
                line_count = lines_needed
            else:
                current_page.append(line)
                current_chars += len(line)
                line_count += lines_needed
            total_lines += lines_needed
        
        # 添加最后一页
        if current_page:
            page_text = ''.join(current_page)
            self.pages.append(page_text)
            self.page_indices.append((current_chars - len(page_text), current_chars))
        
        self.total_pages = len(self.pages)
        
        # 初始化当前页并绘制界面
        self.current_page = 0
        stdscr.clear()
        self.draw_header(stdscr)
        self.draw_text(stdscr)
        self.draw_footer(stdscr)
        
        # 主循环，处理用户输入
        while self.current_pos < self.total_chars:
            # 翻页逻辑
            if self.current_pos >= self.page_indices[self.current_page][1]:
                if self.current_page < self.total_pages - 1:
                    self.current_page += 1
                    stdscr.clear()
                    self.draw_header(stdscr)
                    self.draw_text(stdscr)
                    self.draw_footer(stdscr)
                    continue
                else:
                    break
            
            key = stdscr.getch()
            
            # ESC 退出
            if key == 27:
                self.end_time = time.time()
                return False
            
            # 处理退格键
            if key == curses.KEY_BACKSPACE or key == 127:
                if self.user_input:
                    self.user_input.pop()
                    self.current_pos -= 1
            else:
                char = chr(key)
                self.user_input.append(char)
                if char == self.text[self.current_pos]:
                    self.correct_chars += 1
                else:
                    self.wrong_chars += 1
                self.current_pos += 1
            
            # 刷新界面
            stdscr.clear()
            self.draw_header(stdscr)
            self.draw_text(stdscr)
            self.draw_footer(stdscr)
        
        self.end_time = time.time()
        return True

    # 初始化颜色对
    def init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)  
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE) 
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK) 

    # 绘制头部信息（标题、进度、速度、准确率等）
    def draw_header(self, stdscr):
        height, width = stdscr.getmaxyx()
        title = f"Terminal Typing Exercise - {self.exercise_name}"
        stdscr.addstr(0, (width - len(title)) // 2, title)
        
        progress = f"Progress: {self.current_pos}/{self.total_chars} ({self.current_pos/self.total_chars:.1%})"
        stdscr.addstr(1, (width - len(progress)) // 2, progress)
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        elapsed_str = f"Time elapsed: {elapsed:.1f}s"
        stdscr.addstr(2, (width - len(elapsed_str)) // 2, elapsed_str)
        
        if self.current_pos > 0:
            speed = (self.current_pos / 5) / (elapsed / 60)
            accuracy = self.correct_chars / self.current_pos * 100 if self.current_pos > 0 else 0
            stats = f"Speed: {speed:.1f} WPM | Accuracy: {accuracy:.1f}%"
            stdscr.addstr(3, (width - len(stats)) // 2, stats)
        
        # 显示页码信息
        if self.total_pages > 0:
            page_info = f"Page {self.current_page + 1}/{self.total_pages}"
            stdscr.addstr(4, (width - len(page_info)) // 2, page_info)

    # 绘制当前页的文本内容，带颜色高亮
    def draw_text(self, stdscr):
        if self.total_pages == 0:
            return
            
        height, width = stdscr.getmaxyx()
        y = 5
        current_page_text = self.pages[self.current_page]
        
        page_start, page_end = self.page_indices[self.current_page]
        
        char_index = page_start
        line_idx = 0
        col_idx = 0 
        
        for char in current_page_text:
            if y >= height - 1:
                break
                
            if char_index >= page_end:
                break
                
            if char == '\n':
                y += 1
                line_idx += 1
                col_idx = 0
                char_index += 1
                continue
                
            if y >= 5:
                # 根据输入正确与否设置颜色
                if char_index < self.current_pos:
                    idx_in_page = char_index - page_start
                    if idx_in_page < len(self.user_input):
                        if self.user_input[idx_in_page] == char:
                            color = curses.color_pair(1)
                        else:
                            color = curses.color_pair(2)
                    else:
                        color = curses.color_pair(4)
                elif char_index == self.current_pos:
                    color = curses.color_pair(3)
                else:
                    color = curses.color_pair(5)
                
                try:
                    if col_idx < width:
                        stdscr.addch(y, col_idx, char, color)
                except curses.error:
                    pass
            
            col_idx += 1
            char_index += 1
            
            # 换行处理
            if col_idx >= width:
                y += 1
                line_idx += 1
                col_idx = 0
                
                if line_idx >= self.page_line_count:
                    break

    # 绘制底部提示信息
    def draw_footer(self, stdscr):
        height, width = stdscr.getmaxyx()
        if self.current_page < self.total_pages - 1:
            footer = "Press ESC to quit. Press any key for next page when done"
        else:
            footer = "Press ESC to quit"
        stdscr.addstr(height - 1, (width - len(footer)) // 2, footer)

    # 保存打字记录到文件
    def save_record(self):
        record = {
            "exercise": self.exercise_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration": self.end_time - self.start_time,
            "total_chars": self.total_chars,
            "correct_chars": self.correct_chars,
            "wrong_chars": self.wrong_chars,
            "accuracy": self.correct_chars / self.total_chars * 100 if self.total_chars > 0 else 0,
            "speed_wpm": (self.total_chars / 5) / ((self.end_time - self.start_time) / 60),
        }
        
        record_file = self.records_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.exercise_name}.json"
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        
        return record

# 结果展示函数
def show_results(stdscr, record):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    title = "Exercise Results"
    stdscr.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD)
    
    lines = [
        f"Exercise: {record['exercise']}",
        f"Completion time: {record['date']}",
        f"Duration: {record['duration']:.1f} seconds",
        f"Total characters: {record['total_chars']}",
        f"Correct characters: {record['correct_chars']}",
        f"Wrong characters: {record['wrong_chars']}",
        f"Accuracy: {record['accuracy']:.1f}%",
        f"Typing speed: {record['speed_wpm']:.1f} WPM (words per minute)",
        "",
        "Press any key to exit..."
    ]
    
    for i, line in enumerate(lines):
        stdscr.addstr(3 + i, (width - len(line)) // 2, line)
    
    stdscr.getch()

# 主入口函数
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ttp <exercise_name>")
        print("Available exercises:")
        exercises_dir = Path("./exercises")
        if exercises_dir.exists():
            for f in exercises_dir.glob("*.txt"):
                print(f"  - {f.stem}")
        sys.exit(1)
    
    exercise_name = sys.argv[1]
    exercise = TypingExercise(exercise_name)
    
    completed = curses.wrapper(exercise.run)
    
    if completed:
        record = exercise.save_record()
        curses.wrapper(show_results, record)
    else:
        print("\nExercise canceled.")

if __name__ == "__main__":
    main()