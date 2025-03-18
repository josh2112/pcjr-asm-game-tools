NASM="$(USERPROFILE)\AppData\Local\bin\NASM\nasm.exe"
DOSBOX="..\..\dosbox\dosbox.exe"
DOSBOX_DBG="..\..\dosbox\dosbox_with_debugger.exe"
RM=cmd \/C del

STD=..\..\..\pcjr-asm-game-future\std

TARGET=test
TARGET.COM=$(TARGET).com

DEPS=$(STD)\stdio.mac.asm $(STD)\stdio.asm

NASM_OPTS=-f bin -l $(TARGET).lst
DOSBOX_OPTS=-conf "..\..\pcjr.dosbox.conf"

$(TARGET.COM): $(TARGET).asm $(DEPS)
	$(NASM) $(NASM_OPTS) -o $@ $<

run: $(TARGET.COM)
	$(DOSBOX) $(DOSBOX_OPTS) $^

dosbox:  $(TARGET.COM)	# Just open dosbox, don't run
	$(DOSBOX) $(DOSBOX_OPTS) -c "mount c: ." -c "c:"

debug: $(TARGET.COM)	# Debug with dosbox's built-in debugger
	$(DOSBOX_DBG) $(DOSBOX_OPTS) -c "mount c: ." -c "c:" -c "debug $^"

clean:
	$(RM) $(TARGET.COM) $(TARGET).lst
