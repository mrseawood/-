import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import threading
import queue

class WatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("照片水印添加工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置变量
        self.source_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.watermark_path = tk.StringVar()
        self.position = tk.StringVar(value="右下角")
        self.opacity = tk.IntVar(value=50)
        self.watermark_size = tk.IntVar(value=30)
        self.horizontal_offset = tk.IntVar(value=0)  # 水平偏移量（像素）
        self.vertical_offset = tk.IntVar(value=0)    # 垂直偏移量（像素）
        self.processed_files = 0
        self.total_files = 0
        self.processing_queue = queue.Queue()
        self.preview_image = None
        self.original_preview_image = None  # 保存原始预览图像用于实时更新
        
        # 创建界面
        self.create_widgets()
        
        # 绑定窗口大小变化事件
        self.root.bind("<Configure>", self.on_window_resize)
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="设置", padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 源文件夹选择
        ttk.Label(control_frame, text="源文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(control_frame, textvariable=self.source_folder, width=30).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(control_frame, text="浏览...", command=self.browse_source).grid(row=0, column=2, pady=5)
        
        # 输出文件夹选择
        ttk.Label(control_frame, text="输出文件夹:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(control_frame, textvariable=self.output_folder, width=30).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(control_frame, text="浏览...", command=self.browse_output).grid(row=1, column=2, pady=5)
        
        # 水印图片选择
        ttk.Label(control_frame, text="水印图片:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(control_frame, textvariable=self.watermark_path, width=30).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(control_frame, text="浏览...", command=self.browse_watermark).grid(row=2, column=2, pady=5)
        
        # 水印位置选择
        ttk.Label(control_frame, text="水印位置:").grid(row=3, column=0, sticky=tk.W, pady=5)
        positions = ["左上角", "右上角", "左下角", "右下角", "居中"]
        position_combo = ttk.Combobox(control_frame, textvariable=self.position, values=positions, state="readonly", width=28)
        position_combo.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        position_combo.bind("<<ComboboxSelected>>", self.update_preview_on_change)  # 添加下拉框选择事件绑定
        
        # 水印透明度
        ttk.Label(control_frame, text="透明度:").grid(row=4, column=0, sticky=tk.W, pady=5)
        opacity_frame = ttk.Frame(control_frame)
        opacity_frame.grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=5)
        opacity_scale = ttk.Scale(opacity_frame, from_=0, to=100, variable=self.opacity, orient=tk.HORIZONTAL, length=200)
        opacity_scale.pack(side=tk.LEFT)
        opacity_scale.bind("<B1-Motion>", self.update_preview_on_change)  # 拖动时更新预览
        opacity_scale.bind("<ButtonRelease-1>", self.update_preview_on_change)  # 释放鼠标时更新预览
        # 创建一个新的StringVar来显示整数值
        self.opacity_display = tk.StringVar()
        self.opacity.trace_add("write", lambda *args: self.opacity_display.set(str(int(self.opacity.get()))))
        self.opacity_display.set(str(int(self.opacity.get())))
        ttk.Label(opacity_frame, textvariable=self.opacity_display).pack(side=tk.LEFT, padx=5)
        
        # 水印大小
        ttk.Label(control_frame, text="水印大小(%):").grid(row=5, column=0, sticky=tk.W, pady=5)
        size_frame = ttk.Frame(control_frame)
        size_frame.grid(row=5, column=1, columnspan=2, sticky=tk.W, pady=5)
        size_scale = ttk.Scale(size_frame, from_=5, to=100, variable=self.watermark_size, orient=tk.HORIZONTAL, length=200)
        size_scale.pack(side=tk.LEFT)
        size_scale.bind("<B1-Motion>", self.update_preview_on_change)  # 拖动时更新预览
        size_scale.bind("<ButtonRelease-1>", self.update_preview_on_change)  # 释放鼠标时更新预览
        # 创建一个新的StringVar来显示整数值
        self.watermark_size_display = tk.StringVar()
        self.watermark_size.trace_add("write", lambda *args: self.watermark_size_display.set(str(int(self.watermark_size.get()))))
        self.watermark_size_display.set(str(int(self.watermark_size.get())))
        ttk.Label(size_frame, textvariable=self.watermark_size_display).pack(side=tk.LEFT, padx=5)
        
        # 水平偏移量
        ttk.Label(control_frame, text="水平偏移量:").grid(row=6, column=0, sticky=tk.W, pady=5)
        h_offset_frame = ttk.Frame(control_frame)
        h_offset_frame.grid(row=6, column=1, columnspan=2, sticky=tk.W, pady=5)
        h_offset_scale = ttk.Scale(h_offset_frame, from_=-100, to=100, variable=self.horizontal_offset, orient=tk.HORIZONTAL, length=200)
        h_offset_scale.pack(side=tk.LEFT)
        h_offset_scale.bind("<B1-Motion>", self.update_preview_on_change)  # 拖动时更新预览
        h_offset_scale.bind("<ButtonRelease-1>", self.update_preview_on_change)  # 释放鼠标时更新预览
        # 创建一个新的StringVar来显示整数值
        self.h_offset_display = tk.StringVar()
        self.horizontal_offset.trace_add("write", lambda *args: self.h_offset_display.set(str(int(self.horizontal_offset.get()))))
        self.h_offset_display.set(str(int(self.horizontal_offset.get())))
        ttk.Label(h_offset_frame, textvariable=self.h_offset_display).pack(side=tk.LEFT, padx=5)
        
        # 垂直偏移量
        ttk.Label(control_frame, text="垂直偏移量:").grid(row=7, column=0, sticky=tk.W, pady=5)
        v_offset_frame = ttk.Frame(control_frame)
        v_offset_frame.grid(row=7, column=1, columnspan=2, sticky=tk.W, pady=5)
        v_offset_scale = ttk.Scale(v_offset_frame, from_=-100, to=100, variable=self.vertical_offset, orient=tk.HORIZONTAL, length=200)
        v_offset_scale.pack(side=tk.LEFT)
        v_offset_scale.bind("<B1-Motion>", self.update_preview_on_change)  # 拖动时更新预览
        v_offset_scale.bind("<ButtonRelease-1>", self.update_preview_on_change)  # 释放鼠标时更新预览
        # 创建一个新的StringVar来显示整数值
        self.v_offset_display = tk.StringVar()
        self.vertical_offset.trace_add("write", lambda *args: self.v_offset_display.set(str(int(self.vertical_offset.get()))))
        self.v_offset_display.set(str(int(self.vertical_offset.get())))
        ttk.Label(v_offset_frame, textvariable=self.v_offset_display).pack(side=tk.LEFT, padx=5)
        
        # 创建一个新的Frame来容纳预览和处理按钮
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.grid(row=8, column=0, columnspan=3, pady=10)
        
        # 预览按钮和开始处理按钮并排放置
        ttk.Button(buttons_frame, text="预览效果", command=self.preview_watermark).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_frame, text="开始处理", command=self.start_processing).pack(side=tk.LEFT, padx=10)
        
        # 帮助按钮 - 调整到第9行
        ttk.Button(control_frame, text="使用说明", command=self.show_help).grid(row=9, column=0, columnspan=3, pady=10)
        
        # 创建右侧预览和进度区域
        preview_frame = ttk.LabelFrame(main_frame, text="预览和进度", padding="10")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 预览区域
        self.preview_canvas = tk.Canvas(preview_frame, bg="#f0f0f0", highlightthickness=1, highlightbackground="#cccccc")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 进度条和状态
        progress_frame = ttk.Frame(preview_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(progress_frame, text="处理进度:").pack(side=tk.LEFT, padx=5)
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=300, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(preview_frame, textvariable=self.status_var)
        self.status_label.pack(anchor=tk.W, pady=5)
        
        # 版权信息标签
        copyright_label = ttk.Label(self.root, text="© 2025 一模型Ai (https://jmlovestore.com) - 不会开发软件吗 🙂 Ai会哦", font=("Arial", 9))
        copyright_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
    def browse_source(self):
        folder = filedialog.askdirectory(title="选择源文件夹")
        if folder:
            self.source_folder.set(folder)
    
    def browse_output(self):
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder.set(folder)
    
    def browse_watermark(self):
        file_path = filedialog.askopenfilename(title="选择水印图片", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if file_path:
            self.watermark_path.set(file_path)
            # 加载水印图片预览
            self.load_watermark_preview()
    
    def load_watermark_preview(self):
        watermark_path = self.watermark_path.get()
        if watermark_path and os.path.exists(watermark_path):
            try:
                watermark = Image.open(watermark_path)
                # 调整大小以适应预览区域
                watermark.thumbnail((200, 200))
                watermark_tk = ImageTk.PhotoImage(watermark)
                
                # 在预览画布上显示
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(
                    self.preview_canvas.winfo_width() // 2,
                    self.preview_canvas.winfo_height() // 2,
                    image=watermark_tk
                )
                self.preview_image = watermark_tk  # 保持引用以防止垃圾回收
                
                self.status_var.set(f"已加载水印图片: {os.path.basename(watermark_path)}")
            except Exception as e:
                messagebox.showerror("错误", f"无法加载水印图片: {str(e)}")
    
    def preview_watermark(self):
        # 检查是否已选择水印图片
        if not self.watermark_path.get() or not os.path.exists(self.watermark_path.get()):
            messagebox.showwarning("警告", "请先选择水印图片")
            return
        
        # 打开文件对话框选择一张图片进行预览
        preview_file = filedialog.askopenfilename(title="选择一张图片进行预览", 
                                                filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not preview_file:
            return
            
        try:
            # 加载原图和水印
            original = Image.open(preview_file)
            # 保存原始图像用于实时预览
            self.original_preview_image = original.copy()
            
            # 加载水印图片
            watermark = Image.open(self.watermark_path.get())
            
            # 应用水印
            result = self.apply_watermark(original, watermark)
            
            # 调整大小以适应预览区域
            max_size = (self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height())
            result.thumbnail(max_size)
            
            # 显示预览
            result_tk = ImageTk.PhotoImage(result)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                self.preview_canvas.winfo_width() // 2,
                self.preview_canvas.winfo_height() // 2,
                image=result_tk
            )
            self.preview_image = result_tk  # 保持引用以防止垃圾回收
            
            self.status_var.set(f"已预览: {os.path.basename(preview_file)}")
        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {str(e)}")
    
    def on_window_resize(self, event=None):
        """当窗口大小变化时调整预览图"""
        # 确保事件来自主窗口而不是子组件
        if event.widget == self.root:
            # 如果有预览图，则重新调整大小
            self.update_preview_on_change()
    
    def update_preview_on_change(self, event=None):
        """当设置改变时更新预览"""
        if self.original_preview_image is not None and self.watermark_path.get() and os.path.exists(self.watermark_path.get()):
            try:
                # 加载水印图片
                watermark = Image.open(self.watermark_path.get())
                
                # 应用水印
                result = self.apply_watermark(self.original_preview_image.copy(), watermark)
                
                # 调整大小以适应预览区域
                max_size = (self.preview_canvas.winfo_width(), self.preview_canvas.winfo_height())
                result.thumbnail(max_size)
                
                # 显示预览
                result_tk = ImageTk.PhotoImage(result)
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(
                    self.preview_canvas.winfo_width() // 2,
                    self.preview_canvas.winfo_height() // 2,
                    image=result_tk
                )
                self.preview_image = result_tk  # 保持引用以防止垃圾回收
            except Exception as e:
                # 预览更新失败时不显示错误对话框，只更新状态
                self.status_var.set(f"预览更新失败: {str(e)}")
    
    def apply_watermark(self, image, watermark):
        """将水印应用到图像上"""
        # 创建图像副本
        result = image.copy()
        
        # 调整水印大小
        watermark_size_percent = self.watermark_size.get() / 100.0
        new_width = int(result.width * watermark_size_percent)
        new_height = int(watermark.height * (new_width / watermark.width))
        watermark = watermark.resize((new_width, new_height), Image.LANCZOS)
        
        # 创建透明水印
        opacity = self.opacity.get() / 100.0
        if watermark.mode != 'RGBA':
            watermark = watermark.convert('RGBA')
        
        # 创建透明图层
        alpha = watermark.split()[3]
        alpha = alpha.point(lambda p: int(p * opacity))
        watermark.putalpha(alpha)
        
        # 确定水印位置
        position = self.position.get()
        h_offset = self.horizontal_offset.get()
        v_offset = self.vertical_offset.get()
        
        if position == "左上角":
            pos = (0 + h_offset, 0 + v_offset)
        elif position == "右上角":
            pos = (result.width - watermark.width + h_offset, 0 + v_offset)
        elif position == "左下角":
            pos = (0 + h_offset, result.height - watermark.height + v_offset)
        elif position == "右下角":
            pos = (result.width - watermark.width + h_offset, result.height - watermark.height + v_offset)
        else:  # 居中
            pos = ((result.width - watermark.width) // 2 + h_offset, 
                   (result.height - watermark.height) // 2 + v_offset)
        
        # 粘贴水印
        if result.mode != 'RGBA':
            result = result.convert('RGBA')
        
        # 创建透明图层并粘贴水印
        transparent = Image.new('RGBA', result.size, (0, 0, 0, 0))
        transparent.paste(watermark, pos)
        
        # 合并图层
        result = Image.alpha_composite(result, transparent)
        
        return result
    
    def start_processing(self):
        """开始批量处理图片"""
        # 检查必要的输入
        if not self.source_folder.get() or not os.path.exists(self.source_folder.get()):
            messagebox.showwarning("警告", "请选择有效的源文件夹")
            return
        
        if not self.output_folder.get():
            messagebox.showwarning("警告", "请选择输出文件夹")
            return
        
        if not self.watermark_path.get() or not os.path.exists(self.watermark_path.get()):
            messagebox.showwarning("警告", "请选择水印图片")
            return
            
        # 创建输出文件夹（如果不存在）
        output_folder = self.output_folder.get()
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # 获取所有图片文件
        source_folder = self.source_folder.get()
        image_files = []
        for root, _, files in os.walk(source_folder):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            messagebox.showinfo("信息", "源文件夹中没有找到图片文件")
            return
        
        # 设置进度条
        self.total_files = len(image_files)
        self.processed_files = 0
        self.progress_bar["maximum"] = self.total_files
        self.progress_bar["value"] = 0
        
        # 加载水印图片
        try:
            watermark = Image.open(self.watermark_path.get())
        except Exception as e:
            messagebox.showerror("错误", f"无法加载水印图片: {str(e)}")
            return
        
        # 将图片文件添加到处理队列
        for image_file in image_files:
            self.processing_queue.put(image_file)
        
        # 启动处理线程
        self.status_var.set("正在处理图片...")
        threading.Thread(target=self.process_images, args=(watermark,), daemon=True).start()
        
    def show_help(self):
        """显示使用说明对话框"""
        help_text = """
照片水印添加工具 - 使用说明

基本操作步骤：
1. 选择源文件夹：点击"浏览..."按钮选择包含需要添加水印的图片的文件夹
2. 选择输出文件夹：点击"浏览..."按钮选择处理后图片的保存位置
3. 选择水印图片：点击"浏览..."按钮选择水印图片（推荐使用PNG格式的透明背景图片）
4. 设置水印参数：
   - 水印位置：选择水印在图片中的位置（左上角、右上角、左下角、右下角、居中）
   - 透明度：调整水印的透明度（0-100，数值越小越透明）
   - 水印大小：调整水印相对于原图的大小比例（5%-100%）
   - 水平偏移量：调整水印的水平位置（-100到100像素）
   - 垂直偏移量：调整水印的垂直位置（-100到100像素）
5. 预览效果：点击"预览效果"按钮，选择一张图片进行预览
6. 开始处理：点击"开始处理"按钮开始批量处理所有图片

注意事项：
- 程序会递归处理源文件夹中的所有子文件夹
- 支持的图片格式：PNG、JPG、JPEG、BMP
- 调整参数时，如果有预览图片，可以实时查看效果变化
- 处理大量图片可能需要一些时间，请耐心等待
- 处理过程中可以查看进度条和状态信息
        """
        
        # 创建对话框
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("使用说明")
        help_dialog.geometry("600x500")
        help_dialog.resizable(True, True)
        help_dialog.transient(self.root)  # 设置为主窗口的子窗口
        help_dialog.grab_set()  # 模态对话框
        
        # 创建文本区域
        text_frame = ttk.Frame(help_dialog, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建文本控件
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # 插入帮助文本
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)  # 设置为只读
        
        # 添加关闭按钮
        ttk.Button(help_dialog, text="关闭", command=help_dialog.destroy).pack(pady=10)
    
    def process_images(self, watermark):
        """处理队列中的所有图片"""
        try:
            # 处理队列中的所有图片
            while not self.processing_queue.empty():
                # 获取下一个图片文件
                image_file = self.processing_queue.get()
                
                try:
                    # 构建输出文件路径
                    rel_path = os.path.relpath(image_file, self.source_folder.get())
                    output_file = os.path.join(self.output_folder.get(), rel_path)
                    
                    # 确保输出目录存在
                    output_dir = os.path.dirname(output_file)
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    
                    # 加载图片
                    image = Image.open(image_file)
                    
                    # 应用水印
                    result = self.apply_watermark(image, watermark)
                    
                    # 保存结果
                    if result.mode == 'RGBA' and output_file.lower().endswith(('.jpg', '.jpeg')):
                        # JPEG不支持透明度，转换为RGB
                        result = result.convert('RGB')
                    
                    result.save(output_file)
                    
                    # 更新进度
                    self.processed_files += 1
                    self.progress_bar["value"] = self.processed_files
                    
                    # 更新状态
                    self.status_var.set(f"正在处理: {os.path.basename(image_file)} ({self.processed_files}/{self.total_files})")
                    
                    # 更新UI
                    self.root.update_idletasks()
                    
                except Exception as e:
                    # 记录错误但继续处理其他图片
                    print(f"处理图片 {image_file} 时出错: {str(e)}")
                    messagebox.showerror("错误", f"处理图片 {os.path.basename(image_file)} 时出错: {str(e)}")
                
                # 标记任务完成
                self.processing_queue.task_done()
            
            # 所有图片处理完成
            self.status_var.set(f"处理完成! 共处理 {self.processed_files} 张图片")
            messagebox.showinfo("完成", f"所有图片处理完成! 共处理 {self.processed_files} 张图片")
            
        except Exception as e:
            # 处理过程中的一般错误
            self.status_var.set(f"处理过程中出错: {str(e)}")
            messagebox.showerror("错误", f"处理过程中出错: {str(e)}")