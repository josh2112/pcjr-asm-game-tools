memory_model = -mc
compile_options = -0 $(memory_model) -oh -os -s -zp2 -zpw


objs = mcblist.obj

all : mcblist.exe

clean : .symbolic
  @del mcblist.exe
  @del *.obj
  @del *.map

#patch : .symbolic
#  ..\..\utils\patch jrecv.exe jrecv.map $(memory_model)

#.asm : $(tcp_c_dir)

#.cpp : $(tcp_c_dir)

#.asm.obj :
#  wasm -0 $(memory_model) $[*

.c.obj :
  wcc $[* $(compile_options)

mcblist.exe: $(objs)
  wlink system dos option map option stack=4096 name $@ file *.obj

shrink: mcblist.exe
  ..\tools\upx\upx.exe mcblist.exe