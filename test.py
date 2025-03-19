import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import random
from PIL import Image, ImageTk
import sys
import random

class HanziAdventure:
    def __init__(self,Name="",Name2="汉字秘境闯关",Name3="",close=False,password="######"):
        self.window = tk.Tk()
        self.window.title(str(Name)+str(Name2)+str(Name3))
        self.window.geometry("800x600")
        self.score_default = False  # 初始化 score_default

        # 添加设置按钮，放在底部正中间
        self.settings_button = ttk.Button(self.window, text="⚙️ 设置", command=self.show_settings_window)
        self.settings_button.place(relx=0.5, rely=1.0, anchor='s', y=-10)

        # 加载题库
        with open('questions.json', 'r', encoding='utf-8') as f:
            self.questions = json.load(f)

        self.score = 0
        # 初始化默认时间为 10 分钟
        self.DEFAULT_TIME_SECOND = 600 # 10 * 60
        self.time_left = self.DEFAULT_TIME_SECOND
        self.used_questions = {
            "xiehouyu": set(),
            "riddles": set()
        }  # 记录已使用的题目索引
        self.rule_window = None  # 规则窗口
        self.version_window = None  # 版本更新窗口  # 新增
        self.current_question_type = None  # 当前题目类型
        self.current_question = None  # 当前题目


        self.commands = {}
        self.commands_open = False
        self.default_command = None

        self.exit=False
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)  # 绑定窗口关闭事件
        
        self.random_min=1
        self.random_max=7

        # 创建界面
        self.create_welcome_page()


    def clear_window(self):
        """清除窗口中的所有内容"""
        if hasattr(self, 'timer_id'):  # 如果计时器存在
            self.window.after_cancel(self.timer_id)  # 停止计时器
        for widget in self.window.winfo_children():
            if widget != self.settings_button:  # 保留设置按钮
                widget.destroy()
        # 确保设置按钮始终在底部正中间
        self.settings_button.lift()  # 将按钮置于最上层
        self.settings_button.place(relx=0.5, rely=1.0, anchor='s', y=-10)


    def create_welcome_page(self):
        """创建欢迎页面"""
        self.clear_window()
        # 重置已使用的题目索引
        for key in self.used_questions:
            self.used_questions[key] = set()
        tk.Label(self.window, text="汉字秘境探险", font=("楷体", 36)).pack(pady=50)
        ttk.Button(self.window, text="开始挑战", command=self.main_game_loop).pack(pady=10)
        ttk.Button(self.window, text="挑战规则", command=self.show_rules).pack(pady=10)
        ttk.Button(self.window, text="更新谜语版本", command=self.show_version_window).pack(pady=10)  # 删除这行代码：self.settings_button.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)


    def load_questions(self):
        """加载题库"""
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                self.questions = json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"加载题库失败: {str(e)}")
            self.questions = {"xiehouyu": [], "riddles": []}


    def show_version_window(self):
        """显示版本更新窗口"""
        if self.version_window is not None and self.version_window.winfo_exists():
            return  # 如果窗口已经存在，则不再创建

        self.version_window = tk.Toplevel(self.window)
        self.version_window.title("更新谜语版本")
        self.version_window.geometry("400x300")

        # 显示当前版本信息
        version = self.get_current_version()
        tk.Label(self.version_window, text=f"当前版本: {version}", font=("楷体", 14)).pack(pady=20)

        # 选择新题库文件
        ttk.Button(self.version_window, text="选择新题库文件", command=self.select_new_questions_file).pack(pady=10)

        # 关闭窗口时重置变量
        self.version_window.protocol("WM_DELETE_WINDOW", self.close_version_window)


    def get_current_version(self):
        """获取当前版本"""
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("version", "未知")
        except:
            # 如果当前打开了加载题库默认的 questions.json 文件，返回 questions.json 文件的版本号
            try:
                with open('questions.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("version", "未知")
            except:
                return "未知"


    def select_new_questions_file(self):
        """选择新的题库文件"""
        file_path = tk.filedialog.askopenfilename(
            title="选择题库文件",
            filetypes=[("JSON 文件", "*.json")],
            initialdir="."
        )
        if file_path:
            if self.validate_questions_file(file_path):
                self.questions_file = file_path
                self.load_questions()
                messagebox.showinfo("成功", "题库文件已选择！")
                self.version_window.destroy()
            else:
                messagebox.showerror("错误", "选择的题库文件格式不正确")


    def validate_questions_file(self, file_path):
        """验证题库文件格式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "xiehouyu" in data and "riddles" in data:
                    return True
                return False
        except:
            return False


    def close_version_window(self):
        """关闭版本更新窗口"""
        self.version_window.destroy()
        self.version_window = None


    def create_game_frame(self):
        """创建游戏主框架"""
        self.top_frame = tk.Frame(self.window)
        self.top_frame.pack(fill=tk.X)

        self.score_label = tk.Label(self.top_frame, text=f"积分: {self.score}")
        self.score_label.pack(side=tk.LEFT)

        self.timer_label = tk.Label(self.top_frame, text="剩余时间: 20:00")
        self.timer_label.pack(side=tk.RIGHT)

        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # 底部按钮
        self.bottom_frame = tk.Frame(self.window)
        self.bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(self.bottom_frame, text="结束挑战", command=self.show_result).pack(side=tk.LEFT, padx=10)
        ttk.Button(self.bottom_frame, text="挑战说明", command=self.show_rules).pack(side=tk.RIGHT, padx=10)


    def update_timer(self):
        """更新计时器"""
        if not hasattr(self, 'timer_label') or not self.timer_label.winfo_exists():
            return  # 如果计时器标签不存在，直接返回

        mins, secs = divmod(self.time_left, 60)
        self.timer_label.config(text=f"剩余时间: {mins:02d}:{secs:02d}")
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_id = self.window.after(1000, self.update_timer)  # 保存计时器 ID
        else:
            self.show_result()


    def show_xiehouyu(self):
        """显示歇后语题目"""
        if len(self.used_questions["xiehouyu"]) >= len(self.questions["xiehouyu"]):
            # 如果没有更多歇后语题目，检查是否还有字谜题目
            if len(self.used_questions["riddles"]) < len(self.questions["riddles"]):
                self.show_riddles()
            else:
                self.show_result()  # 所有题目都用完，直接结束游戏
            return
    
        # 确保 main_frame 存在
        if not hasattr(self, 'main_frame') or not self.main_frame.winfo_exists():
            self.create_game_frame()  # 如果 main_frame 不存在，重新创建
    
        # 随机选择一个未使用过的题目
        available_questions = [
            i for i in range(len(self.questions["xiehouyu"]))
            if i not in self.used_questions["xiehouyu"]
        ]
        question_index = random.choice(available_questions)
        self.current_question = self.questions["xiehouyu"][question_index]
        self.current_question_type = "xiehouyu"
    
        # 检查题目格式是否正确
        if 'first_part' not in self.current_question or 'second_part' not in self.current_question:
            # 记录错误日志
            with open('error_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"歇后语题目格式错误，时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"题目内容: {str(self.current_question)}\n\n")
            
            # 跳过该题目
            self.used_questions["xiehouyu"].add(question_index)
            self.show_xiehouyu()
            return

        self.used_questions["xiehouyu"].add(question_index)

        question = f"{self.current_question['first_part']} —— ?"

        # 清除主框架内容
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # 显示题目
        self.question_label = tk.Label(self.main_frame, text=question, font=("楷体", 24))
        self.question_label.pack(pady=20)

        # 输入框
        self.answer_entry = ttk.Entry(self.main_frame, font=("楷体", 18))
        self.answer_entry.pack(pady=10)

        # 提交按钮
        ttk.Button(self.main_frame, text="提交答案", command=self.check_answer).pack()


    def show_riddles(self):
        """显示字谜题目"""
        if len(self.used_questions["riddles"]) >= len(self.questions["riddles"]):
            # 如果没有更多字谜题目，检查是否还有歇后语题目
            if len(self.used_questions["xiehouyu"]) < len(self.questions["xiehouyu"]):
                self.show_xiehouyu()
            else:
                self.show_result()  # 所有题目都用完，直接结束游戏
            return

        # 确保 main_frame 存在
        if not hasattr(self, 'main_frame') or not self.main_frame.winfo_exists():
            self.create_game_frame()  # 如果 main_frame 不存在，重新创建

        # 随机选择一个未使用过的题目
        available_questions = [
            i for i in range(len(self.questions["riddles"]))
            if i not in self.used_questions["riddles"]
        ]
        question_index = random.choice(available_questions)
        self.current_question = self.questions["riddles"][question_index]
        self.current_question_type = "riddles"

        # 检查题目格式是否正确
        if 'question' not in self.current_question or 'answer' not in self.current_question:
            # 记录错误日志
            with open('error_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"字谜题目格式错误，时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"题目内容: {str(self.current_question)}\n\n")
            
            # 跳过该题目
            self.used_questions["riddles"].add(question_index)
            self.show_riddles()
            return

        self.used_questions["riddles"].add(question_index)

        # 动态计算答案字数
        answer_length = len(self.current_question["answer"])
        question = f"{self.current_question['question']}(答案字数: {answer_length})"

        # 清除主框架内容
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # 显示题目
        self.question_label = tk.Label(self.main_frame, text=question, font=("楷体", 24))
        self.question_label.pack(pady=20)

        # 输入框
        self.answer_entry = ttk.Entry(self.main_frame, font=("楷体", 18))
        self.answer_entry.pack(pady=10)

        # 提交按钮
        ttk.Button(self.main_frame, text="提交答案", command=self.check_answer).pack()


    def check_answer(self):
        """检查答案"""
        user_answer = self.answer_entry.get().strip()

        try:
            if self.current_question_type == "xiehouyu":
                correct_answer = self.current_question["second_part"]
            elif self.current_question_type == "riddles":
                correct_answer = self.current_question["answer"]
        except KeyError:
            with open('error_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"题目格式错误，时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"题目类型: {self.current_question_type}\n")
                f.write(f"题目内容: {str(self.current_question)}\n\n")

                    
                # 更友好的提示并自动跳转到下一题
                messagebox.showwarning("提示", "当前题目数据异常，将自动跳转到下一题")
                self.main_game_loop()
                return

        if user_answer == correct_answer:
            self.score += 10
            self.score_label.config(text=f"积分: {self.score}")
            messagebox.showinfo("正确", "回答正确！")
            self.main_game_loop()  # 答对后直接更新题目
        else:
            self.show_error_buttons()  # 答错后显示按钮


    def show_error_buttons(self):
        """显示答错后的按钮"""
        # 隐藏输入框和提交按钮
        self.answer_entry.pack_forget()
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Button) and widget["text"] == "提交答案":
                widget.pack_forget()

        # 显示按钮
        ttk.Button(self.main_frame, text="重新答题", command=self.reset_question).pack(pady=5)
        ttk.Button(self.main_frame, text="展示答案", command=self.show_answer).pack(pady=5)
        ttk.Button(self.main_frame, text="下一题", command=self.main_game_loop).pack(pady=5)


    def reset_question(self):
        """重新答题"""
        # 清空输入框并重新显示输入框和提交按钮
        self.answer_entry.delete(0, tk.END)
        self.answer_entry.pack(pady=10)
        ttk.Button(self.main_frame, text="提交答案", command=self.check_answer).pack()

        # 隐藏错误按钮
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Button) and widget["text"] in ["重新答题", "展示答案", "下一题"]:
                widget.pack_forget()


    def show_answer(self):
        """展示答案"""
        # 创建自定义对话框
        answer_window = tk.Toplevel(self.window)
        answer_window.title("正确答案")
        
        # 设置答案和寓意文本
        if self.current_question_type == "xiehouyu":
            answer_text = self.current_question["second_part"]
            explanation_text = self.current_question["explanation"]
        elif self.current_question_type == "riddles":
            answer_text = self.current_question["answer"]
            explanation_text = self.current_question.get("explanation", "无解析")  # 添加解析字段，默认为"无解析"
        
        # 答案部分
        tk.Label(answer_window, text="答案：", font=("楷体", 14)).pack(pady=(10, 0))
        answer_box = tk.Text(answer_window, wrap=tk.WORD, height=1, width=20, font=("楷体", 14), bg=self.window.cget("bg"))
        answer_box.insert(tk.END, answer_text)
        answer_box.config(state=tk.DISABLED)  # 设置为只读
        answer_box.pack(padx=20, pady=5)
        
        # 含义部分
        tk.Label(answer_window, text="含义：", font=("楷体", 14)).pack(pady=(10, 0))
        explanation_box = tk.Text(answer_window, wrap=tk.WORD, height=3, width=30, font=("楷体", 14), bg=self.window.cget("bg"))
        explanation_box.insert(tk.END, explanation_text)
        explanation_box.config(state=tk.DISABLED)  # 设置为只读
        explanation_box.pack(padx=20, pady=5)
        
        # 解析部分
        tk.Label(answer_window, text="解析：", font=("楷体", 14)).pack(pady=(10, 0))
        analysis_box = tk.Text(answer_window, wrap=tk.WORD, height=5, width=40, font=("楷体", 14), bg=self.window.cget("bg"))
        analysis_text = self.current_question.get("analysis", "无解析")  # 添加解析字段，默认为"无解析"
        analysis_box.insert(tk.END, analysis_text)
        analysis_box.config(state=tk.DISABLED)  # 设置为只读
        analysis_box.pack(padx=20, pady=5)
        
        # 复制答案按钮
        def copy_answer():
            self.window.clipboard_clear()
            self.window.clipboard_append(answer_text)
            messagebox.showinfo("成功", "答案已复制到剪贴板")
        
        ttk.Button(answer_window, text="复制答案", command=copy_answer).pack(pady=10)
        
        # 关闭按钮
        ttk.Button(answer_window, text="关闭", command=answer_window.destroy).pack(pady=10)


    def show_rules(self):
        """显示挑战说明"""
        if self.rule_window is not None and self.rule_window.winfo_exists():
            return  # 如果规则窗口已经存在，则不再创建

        self.rule_window = tk.Toplevel(self.window)
        self.rule_window.title("挑战说明")
        self.rule_window.geometry("500x300")

        rules_text = """
        游戏规则：
        1. 每次回答一个题目，题目类型包括歇后语、字谜。
        2. 答对一题得10分。
        3. 答错后可以选择重新答题、查看答案或跳过。
        4. 时间结束后或主动结束挑战时显示最终得分。
        """
        #去除空格
        rules_text = rules_text.replace(" ", "")
        tk.Label(self.rule_window, text=rules_text, font=("楷体", 14), justify=tk.LEFT).pack(pady=20)

        # 关闭规则窗口时重置变量
        self.rule_window.protocol("WM_DELETE_WINDOW", self.close_rule_window)


    def close_rule_window(self):
        """关闭规则窗口"""
        self.rule_window.destroy()
        self.rule_window = None


    def show_result(self):
        """显示最终结果"""
        self.clear_window()  # 清除所有窗口内容
        # 重置分数和时间
        if self.score_default:
            self.score = 0
        self.time_left = self.DEFAULT_TIME_SECOND
    
        tk.Label(self.window, text="挑战结束！", font=("楷体", 36)).pack(pady=50)
        tk.Label(self.window, text=f"你的最终得分是: {self.score}", font=("楷体", 24)).pack()
        ttk.Button(self.window, text="重新开始", command=self.create_welcome_page).pack()


    def main_game_loop(self):
        """主游戏逻辑"""
        self.clear_window()  # 清除当前窗口内容，包括结束页
        self.create_game_frame()
        self.update_timer()
        # 确保设置按钮始终可见
        self.settings_button.lift()
        self.settings_button.place(relx=0.5, rely=1.0, anchor='s', y=-10)

        # 重置时间
        self.time_left = self.DEFAULT_TIME_SECOND
    
        # 随机选择一种题目类型
        question_types = ["xiehouyu", "riddles"]
        self.current_question_type = random.choice(question_types)
        if self.current_question_type == "xiehouyu":
            self.show_xiehouyu()
        elif self.current_question_type == "riddles":
            self.show_riddles()


    def run(self):
        """运行程序"""
        self.window.mainloop()


    def show_settings_window(self):
        """显示设置窗口"""
        # 如果设置窗口已经存在且未关闭，则直接返回
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            return

        self.settings_window = tk.Toplevel(self.window)
        self.settings_window.title("设置")
        self.settings_window.geometry("300x220")

        # 添加分数重置选项
        tk.Label(self.settings_window, text="分数设置", font=("楷体", 14)).pack(pady=5)
        self.score_default_var = tk.BooleanVar(value=self.score_default)
        ttk.Checkbutton(self.settings_window, text="每次重新开始重置分数", 
                       variable=self.score_default_var).pack()

        # 添加当前分数设置
        tk.Label(self.settings_window, text="当前分数", font=("楷体", 14)).pack(pady=5)
        self.score_entry = ttk.Entry(self.settings_window)
        self.score_entry.insert(0, str(self.score))
        self.score_entry.pack()

        # 添加时间设置
        tk.Label(self.settings_window, text="默认时间(秒)", font=("楷体", 14)).pack(pady=5)
        self.time_entry = ttk.Entry(self.settings_window)
        self.time_entry.insert(0, str(self.DEFAULT_TIME_SECOND))
        self.time_entry.pack()

        # 保存按钮
        ttk.Button(self.settings_window, text="保存", command=self.save_settings).pack(pady=10)

        # 关闭窗口时重置变量
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings_window)


    def close_settings_window(self):
        """关闭设置窗口"""
        self.settings_window.destroy()
        del self.settings_window


    def save_settings(self):
        """保存设置"""
        try:
            # 更新分数重置选项
            self.score_default = self.score_default_var.get()

            # 更新当前分数
            new_score = int(self.score_entry.get())
            self.score = new_score
            if hasattr(self, 'score_label'):
                self.score_label.config(text=f"积分: {self.score}")

            # 更新默认时间
            new_time = int(self.time_entry.get())
            self.DEFAULT_TIME_SECOND = new_time
            self.time_left = new_time
            if hasattr(self, 'timer_label'):
                mins, secs = divmod(self.time_left, 60)
                self.timer_label.config(text=f"剩余时间: {mins:02d}:{secs:02d}")

            messagebox.showinfo("成功", "设置已保存！")
            self.settings_window.destroy()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")


    def change_variable(self, var_name, new_value, value_type=None):
        if not hasattr(self, var_name):
            return None

        if value_type is not None and not isinstance(new_value, value_type):
            return None

        setattr(self, var_name, new_value)
        return True


    def show_settings_window(self):
        """显示设置窗口"""
        # 如果设置窗口已经存在且未关闭，则直接返回
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            return

        self.settings_window = tk.Toplevel(self.window)
        self.settings_window.title("设置")
        self.settings_window.geometry("300x220")

        # 添加分数重置选项
        tk.Label(self.settings_window, text="分数设置", font=("楷体", 14)).pack(pady=5)
        self.score_default_var = tk.BooleanVar(value=self.score_default)
        ttk.Checkbutton(self.settings_window, text="每次重新开始重置分数", 
                       variable=self.score_default_var).pack()

        # 添加当前分数设置
        tk.Label(self.settings_window, text="当前分数", font=("楷体", 14)).pack(pady=5)
        self.score_entry = ttk.Entry(self.settings_window)
        self.score_entry.insert(0, str(self.score))
        self.score_entry.pack()

        # 添加时间设置
        tk.Label(self.settings_window, text="默认时间(秒)", font=("楷体", 14)).pack(pady=5)
        self.time_entry = ttk.Entry(self.settings_window)
        self.time_entry.insert(0, str(self.DEFAULT_TIME_SECOND))
        self.time_entry.pack()

        # 保存按钮
        ttk.Button(self.settings_window, text="保存", command=self.save_settings).pack(pady=10)

        # 关闭窗口时重置变量
        self.settings_window.protocol("WM_DELETE_WINDOW", self.close_settings_window)


    def save_settings(self):
        """保存设置"""
        try:
            # 更新分数重置选项
            self.score_default = self.score_default_var.get()

            # 更新当前分数
            new_score = int(self.score_entry.get())
            self.score = new_score
            if hasattr(self, 'score_label'):
                self.score_label.config(text=f"积分: {self.score}")

            # 更新默认时间
            new_time = int(self.time_entry.get())
            self.DEFAULT_TIME_SECOND = new_time
            self.time_left = new_time
            if hasattr(self, 'timer_label'):
                mins, secs = divmod(self.time_left, 60)
                self.timer_label.config(text=f"剩余时间: {mins:02d}:{secs:02d}")

            messagebox.showinfo("成功", "设置已保存！")
            self.settings_window.destroy()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")


    def command(self):
        print("/help:显示命令帮助")
        while not self.exit:
            try:
                command = input("请输入命令:")
            except:
                sys.exit()       
            self.compile_command(command)


    def command_exit(self):
        try:
            if not self.window.winfo_exists():
                self.exit = True
                print("/exit")
                print(f"Gui程序已退出")
                print(f"分数:{self.score}")
                print(f"时间:{self.time_left}")

                print("\r",end="")
                sys.exit()
        except:
            self.exit = True
            print("/exit")
            print(f"Gui程序已退出")
            print(f"分数:{self.score}")
            print(f"时间:{self.time_left}")
            print("\r",end="")
            sys.exit()


    def on_window_close(self):
        """窗口关闭时触发"""
        self.window.destroy()  # 关闭窗口
        self.command_exit()  # 调用 command_exit 函数


    def eval_expression(self, expr):
        """
        计算字符串表达式
        :param expr: 字符串表达式
        :return: 计算结果，如果表达式无效则返回None
        """
        try:
            # 只允许数字和基本运算符
            allowed_chars = set('0123456789+-*/%^(). ')
            if not all(char in allowed_chars for char in expr):
                return None
            
            # 将 ^ 替换为 **
            expr = expr.replace('^', '**')
            
            # 使用eval计算表达式
            return eval(expr)
        except:
            return None
        

    def compile_command(self, command=""):
        # 检查命令是否为空
        if command:
            if command[0] == "/":
                # 执行命令
                command = command[1:]

                if command == "exit":
                    self.window.destroy()
                    self.exit = True
                    print(f"程序已退出")
                    print(f"分数:{self.score}")
                    print(f"时间:{self.time_left}")
                    sys.exit()

                if command.startswith("score"):
                    """
                    /score:显示当前分数
                    /score set 10:设置当前分数为10
                    """
                    parts = command.split()
                    if len(parts) == 1:
                        print(f"当前分数:{self.score}")
                    elif len(parts) == 3 and parts[1] == "set" and parts[2].isdigit():
                        self.score = int(parts[2])
                        print(f"当前分数:{self.score}")
                    else:
                        print(f"score命令无效")

                elif command.startswith("time"):
                    """
                    /time:显示当前时间
                    /time set 10:设置当前时间为10秒
                    """
                    parts = command.split()
                    if len(parts) == 1:
                        print(f"当前时间:{self.time_left}")
                    elif len(parts) == 3 and parts[1] == "set" and parts[2].isdigit():
                        self.time_left = int(parts[2])
                        print(f"当前时间:{self.time_left}")
                    else:
                        print(f"time命令无效")
                elif command == "rules":
                    self.show_rules()


                elif command == "settings":
                    self.show_settings_window()
                    return


                elif command.startswith("settings"):
                    parts = command.split()
                    if len(parts) == 3 and parts[1] == "reset_score":
                        if parts[2].upper() == "T":
                            self.score_default = True
                            print(f"已设置为每次重新开始重置分数")
                        elif parts[2].upper() == "F":
                            self.score_default = False
                            print(f"已设置为每次重新开始保存分数")
                        else:
                            print(f"settings命令无效")
                    elif len(parts) == 4 and parts[1] == "score" and parts[2] == "set":
                        try:
                            new_score = int(parts[3])
                            self.score = new_score
                            print(f"当前分数已设置为: {self.score}")
                        except ValueError:
                            print(f"请输入有效的分数")
                    elif len(parts) == 4 and parts[1] == "time" and parts[2] == "set":
                        try:
                            new_time = int(parts[3])
                            self.DEFAULT_TIME_SECOND = new_time
                            self.time_left = new_time
                            print(f"当前时间已设置为: {self.time_left}秒")
                        except ValueError:
                            print(f"请输入有效的时间")
                    else:
                        print(f"settings命令无效")

                elif command.startswith("random"):
                    print(f"随机数生成器(min:{self.random_min},max:{self.random_max})")
                    try:
                        parts = command.split()
                        
                        def get_range(a, b):
                            return (min(a, b), max(a, b))
                        
                        if len(parts) == 1:
                            # /random: 生成1个随机数
                            print(random.randint(self.random_min, self.random_max))
                        elif len(parts) == 2 and parts[1].isdigit():
                            # /random 6: 生成6个随机数
                            count = int(parts[1])
                            print([random.randint(self.random_min, self.random_max) for _ in range(count)])
                        elif len(parts) == 3 and parts[1] == "~":
                            # /random ~ 10: 生成1个随机数，范围为min到10
                            new_max = int(parts[2])
                            min_val, max_val = get_range(self.random_min, new_max)
                            print(random.randint(min_val, max_val))
                        elif len(parts) == 3 and parts[2] == "~":
                            # /random 10 ~: 生成1个随机数，范围为10到max
                            new_min = int(parts[1])
                            min_val, max_val = get_range(new_min, self.random_max)
                            print(random.randint(min_val, max_val))
                        elif len(parts) == 4 and parts[1] == "~":
                            # /random ~ 10 6: 生成6个随机数，范围为min到10
                            new_max = int(parts[2])
                            count = int(parts[3])
                            min_val, max_val = get_range(self.random_min, new_max)
                            print([random.randint(min_val, max_val) for _ in range(count)])
                        elif len(parts) == 4 and parts[2] == "~" and "set" not in parts:
                            # /random 10 ~ 6: 生成6个随机数，范围为10到max
                            new_min = int(parts[1])
                            count = int(parts[3])
                            min_val, max_val = get_range(new_min, self.random_max)
                            print([random.randint(min_val, max_val) for _ in range(count)])
                        elif len(parts) == 4 and parts[1] == "set":
                            if parts[2] == "~" and parts[3] == "~":
                                # /random set ~ ~: 设置随机数范围为min到max
                                self.random_min, self.random_max = get_range(self.random_min, self.random_max)
                                print(f"随机数范围已设置为: {self.random_min} ~ {self.random_max}(没变)")
                            elif parts[2] == "~":
                                # /random set ~ 10: 设置随机数范围为min到10
                                new_max = int(parts[3])
                                self.random_min, self.random_max = get_range(self.random_min, new_max)
                                print(f"随机数范围已设置为: {self.random_min} ~ {self.random_max}")
                            elif parts[3] == "~":
                                # /random set 10 ~: 设置随机数范围为10到max
                                new_min = int(parts[2])
                                self.random_min, self.random_max = get_range(new_min, self.random_max)
                                print(f"随机数范围已设置为: {self.random_min} ~ {self.random_max}")
                            else:
                                # /random set 10 20: 设置随机数范围为10到20
                                new_min = int(parts[2])
                                new_max = int(parts[3])
                                self.random_min, self.random_max = get_range(new_min, new_max)
                                print(f"随机数范围已设置为: {self.random_min} ~ {self.random_max}")
                        else:
                            print("random命令无效")
                    except Exception as e:
                        print(f"发生错误!\n{e}")

                elif command == "help":
                    COMMAND_HELP = """命令帮助:
                    命令格式1:/命令
                    命令格式2:/命令 参数
                    /exit:退出程序
                    /score:显示当前分数
                    /score set 10:设置当前分数为10
                    /time:显示当前时间
                    /time set 10:设置当前时间为10秒
                    /rules:显示游戏规则
                    /settings:打开设置窗口
                    /settings reset_score T/F:设置是否每次重新开始重置分数
                    /settings score set 10:设置当前分数为10
                    /settings time set 10:设置当前时间为10秒
                    min默认为1
                    max默认为7
                    min=1
                    max=7
                    /random:随机生成1个min~max的整数
                    /random 6:随机生成6个min~max的整数
                    /random ~ 10:随机生成随机数,范围为min到10(支持大小颠倒)
                    /random 10 ~:随机生成随机数,范围为10到max(支持大小颠倒)
                    /random ~ 10 6:随机生成6个随机数,范围为min到10(支持大小颠倒)
                    /random 10 ~ 6:随机生成6个随机数,范围为10到max(支持大小颠倒)
                    /random set ~ 10:设置随机数范围,为min到10(支持大小颠倒)
                    /random set 10 ~:设置随机数范围,为10到max(支持大小颠倒)
                    /random set 10 20:设置随机数范围,为10到20(支持大小颠倒)
                    /help:显示帮助信息
                    您还可以来计算表达式,例如输入1+1并回车,程序会返回2
                    """.replace("                    ", "")
                    print(COMMAND_HELP,end="")

                else:
                    print(f"有\"/\"命令无效")
            else:
                Num=self.eval_expression(command)
                if Num!=None:
                    try:
                        print(f"{Num}")
                    except:
                        print(f"表达式命令无效")
                else:
                    print(f"无\"/\"命令无效")
#主程序
if __name__ == "__main__":
    Name=input("请输入人名:")
    app = HanziAdventure(Name=Name+"----")
    app.command()