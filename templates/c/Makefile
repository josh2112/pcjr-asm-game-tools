objs = test.obj

all: test.exe

clean: .symbolic
  @del test.exe
  @del *.obj
  @del *.map

.c.obj:
  wcc $[* -0 -mc -oh -os -s -zp2 -zpw

test.exe: $(objs)
  wlink system dos option map option stack=4096 name $@ file *.obj
  d:\upx\upx.exe test.exe
