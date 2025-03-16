[cpu 8086]
[org 100h]

%include '../../pcjr-asm-game/std/stdio.mac'

section .data

str_ok:    db 'allocated memory at segment $'
str_error: db 'error $'
str_largest: db 'largest block avail: $'

section .text

call alloc
call alloc
mov ax, 0x4c00
int 21h

alloc:
mov ax, 4800h
mov bx, 690h ; 6900h, or 26880 bytes
int 21h
jc .error
intToString buf16, ax
print str_ok
println buf16
ret

.error:
push bx
push ax
intToString buf16, ax
print str_error
println buf16
pop ax
pop bx
cmp ax, 8
jne end
intToString buf16, bx
print str_largest
println buf16

end:
ret



%include '../../pcjr-asm-game/std/stdlib.asm'