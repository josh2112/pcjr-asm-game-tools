; Build with:
; . "$env:USERPROFILE\AppData\Local\bin\NASM\nasm.exe" -f bin -o scancode.com .\scancode.asm
; Run with:
; . "..\EmuCR-Dosbox-r4059\dosbox.exe" -conf ..\..\dosbox.conf scancode.com

[cpu 8086]
[org 100h]

%define KEYCODE_ESC 0x01

section .data

  is_running: db 1
  buf: db '0000',0xa,0xd,0

section .text

; Prints the given '$'-terminated string.
%macro print 1
	mov dx, %1
	mov ax, 0x0900
	int 21h
%endmacro

; Prints the given '$'-terminated string and newline.
%macro println 1
	print %1
	print str_crlf
%endmacro

getkey:
mov ah, 1     ; Check for keystroke.  If ZF is set, no keystroke.
int 16h
jz getkey
mov ah, 0     ; Get the keystroke. AH = scan code, AL = ASCII char
int 16h

cmp ah, KEYCODE_ESC
jne .cont
mov byte [is_running], 0

.cont:
mov dx, ax
call print_hex

cmp byte [is_running], 0    ; If still running (ESC key pressed), loop
jne getkey

; Exit the program
mov ax, 0x4c00
int 21h

; Prints the value of DX as hex.
print_hex:
  push ax           ; save the register values to the stack for later
  push cx
  push dx
  push bx

  mov si, buf
  
  mov cx,0          ; start a counter of how many nibbles we've processed, stop at 4

next_character:
        ; increment the counter for each nibble
        inc cx

        ; isolate this nibble
        mov bx, dx
        and bx, 0xf000
        shr bx, 1
        shr bx, 1
        shr bx, 1
        shr bx, 1

        ; add 0x30 to get the ASCII digit value
        add bh, 0x30

        ; If our hex digit was > 9, it'll be > 0x39, so add 7 to get
        ; ASCII letters
        cmp bh, 0x39
        jg add_7

add_character_hex:
        ; put the current nibble into our string template
        mov [si], bh

        ; increment our template string's char position
        inc si

        ; shift dx by 4 to start on the next nibble (to the right)
        shl dx, 1
        shl dx, 1
        shl dx, 1
        shl dx, 1

        ; exit if we've processed all 4 nibbles, else process the next
        ; nibble
        cmp cx, 4
        jnz next_character
        jmp _done

_done:
        ; copy the current nibble's ASCII value to a char in our template
        ; string
        mov bx, buf

        ; print our template string
        call print_string

        pop bx            ; Pop all the registers back onto the stack
        pop dx
        pop cx
        pop ax

        ; return from subroutine
        ret

add_7:
        ; add 7 to our current nibble's ASCII value, in order to get letters
        add bh, 0x7

        ; add the current nibble's ASCII
        jmp add_character_hex


print_string:     ; Push registers onto the stack
  push ax           ; save the register values to the stack for later
  push cx
  push dx
  push bx

string_loop:
  mov al, [bx]    ; Set al to the value at bx
  cmp al, 0       ; Compare the value in al to 0 (check for null terminator)
  jne print_char  ; If it's not null, print the character at al
                  ; Otherwise the string is done, and the function is ending
  pop bx            ; Pop all the registers back onto the stack
pop dx
pop cx
pop ax
  ret             ; return execution to where we were

print_char:
  mov ah, 0x0e    ; Linefeed printing
  int 0x10        ; Print character
  add bx, 1       ; Shift bx to the next character
  jmp string_loop ; go back to the beginning of our loop