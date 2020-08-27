# exebinder

EXE 文件捆绑器：将两个exe绑定为一个exe文件。

Bind 2 Windows exe files to 1 exe file.

支持添加UAC权限声明，支持自定义文件描述，支持自定义图标（如果没有指定，则默认使用被捆绑程序的图标）。

Support bind UAC statement. Support customized file description. Support customized file icon.(use the primary file icon by default)


## 需要MinGW环境。
Need MinGW env. 

因为本程序用到了g++/windres/strip等控制台程序，推荐使用 tdm-gcc。

Cause g++/windres/strip prog be used, and TDM-GCC is recommended.
