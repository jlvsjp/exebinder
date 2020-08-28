# EXE文件捆绑器 - exebinder

将一个exe文件绑定到另一个文件上，支持PE或其他文件，如docx、pdf等。

Bind 1 exe file (secondary) to another file (primary), the primary file type can be docx/pdf etc.

本工具支持添加UAC权限声明，支持自定义文件描述，支持自定义图标（如果没有指定，则默认使用被捆绑程序的图标），支持不落地加载被捆绑文件。

This tool supports binding UAC statement. Supports customized file description. Supports customized file icon.(use the primary file icon by default). And Supports load binded exe file from memory.


## 需要MinGW环境。

Need MinGW env. 

因为本程序用到了g++/windres/strip等控制台程序，推荐使用 tdm-gcc。

Cause g++/windres/strip prog be used, and TDM-GCC is recommended.

## 不落地加载

Load image from memory.

建议先使用file命令查看一下需要捆绑的文件的架构。

I suggest before use this tool, you may check the architecture of the secondary file(the binded exe file) by use `file` command or other similar tool.

例如：如果是Windows 80386 的 console 程序，则需要指定--x86 和 --no-gui 参数。

For example, if the secondary file is Windows 80386 console program, you need run `python exebinder.py` with `--x86` and `--no-gui` flags.
