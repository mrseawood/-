# 照片水印添加工具

这是一个用Python开发的照片批量添加水印工具，可以递归处理文件夹中的所有图片。

## 功能特点

- 支持批量处理图片文件
- 递归处理子文件夹中的图片
- 可自定义水印位置（左上角、右上角、左下角、右下角、居中）
- 可调整水印透明度
- 可调整水印大小
- 实时预览水印效果
- 处理进度显示

## 使用方法

1. 运行`main.py`启动程序
2. 选择源文件夹（包含需要添加水印的图片）
3. 选择输出文件夹（处理后的图片将保存在这里）
4. 选择水印图片（推荐使用PNG格式的透明背景图片）
5. 设置水印位置、透明度和大小
6. 点击"预览效果"按钮可以预览水印效果
7. 点击"开始处理"按钮开始批量处理

## 依赖库

- tkinter (GUI界面)
- Pillow (图像处理)

## 安装依赖

```
pip install pillow
```

tkinter通常随Python一起安装，无需单独安装。

![123](https://github.com/user-attachments/assets/4fc5e21b-b3aa-46cb-b0bf-f9a757b6ead5)
