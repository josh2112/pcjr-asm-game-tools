; Build with:
; . nasm -f bin -o test.com .\test.asm
; Run with:
; . "..\EmuCR-Dosbox-r4059\dosbox.exe" -conf ..\..\dosbox.conf scancode.com


[cpu 8086]
[org 100h]

section .text

top: push ax
