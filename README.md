# exebinder

EXE 文件捆绑器：将两个exe绑定为一个exe文件。

Bind 2 Windows exe files to 1 exe file.

支持添加UAC权限声明，支持自定义文件描述，支持自定义图标（如果没有指定，则默认使用被捆绑程序的图标）。

Support bind UAC statement. Support customized file description. Support customized file icon.(use the primary file icon by default)


## 需要MinGW环境。
Need MinGW env. 

因为本程序用到了g++/windres/strip等控制台程序，推荐使用 tdm-gcc。

Cause g++/windres/strip prog be used, and TDM-GCC is recommended.

## 不落地加载
Load image from memory.

建议先使用file命令查看一下需要捆绑的文件的架构。
I suggest before use this tool, you may check the architecture of the secondary file(the binded exe file) by use `file` command or other similar tool.

例如：如果是Windows 80386 的 console 程序，则需要指定--x86，但不需要指定--gui.
For example, if it is Windows 80386 console program, you need run `python exebinder.py` with `--x86` flag, but `--gui` is not need.
