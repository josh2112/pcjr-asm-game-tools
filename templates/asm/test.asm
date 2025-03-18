[cpu 8086]
[org 100h]

%include '../../../pcjr-asm-game-future/std/stdio.mac.asm'

section .data

str_hello:    db 'Hello world!$'
str_pressKey: db 'Press any key to quit...$'
section .text

println str_hello
println str_pressKey
waitForAnyKey

; Exit the program
mov ax, 4c00h
int 21h

%include '../../../pcjr-asm-game-future/std/stdio.asm'