@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
cl /Bv /std:c++20 /EHsc /W4 /WX /I delta-core-cpp/include harness.cpp delta-core-cpp/src/consensus.cpp delta-core-cpp/src/canonical.cpp delta-core-cpp/src/sha256.cpp delta-core-cpp/src/certificates/contracts.cpp /Fe:available-q.exe
exit /b %errorlevel%
