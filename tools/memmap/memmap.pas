{$M 4000,0,0}
PROGRAM MemMap;

 {MemMap shows a Memory Map of all programs and environment blocks.

  Usage:  MEMMAP       to show all Memory Control Blocks (MCBs)
        or
          MEMMAP /V    to show MCBs and all environment variables
                       (the /V option is ignored in DOS 2.X or lower)

  (C) Copyright 1989, Earl F. Glynn, Overland Park, KS.
  All Rights Reserved.

  This program may be freely distributed for non-commercial use.

  MemMap is based on PCMAP from PC Magazine, SHOWMEM from "The
  Waite's Group MS-DOS Developer's Guide" (Second Edition), and
  the DOS 4.0  MEM /DEBUG  command.

  Version 1.0 -- 27 February 1989.

  Version 2.0 -- 17 May 1989.
    Modifications were made to handle IBM's INDCIPL program (part of
    the 3270 Workstation Program).  Memory with it has a large number
    of contiguous MCBs each pointing to a zero-length block.  Termination
    conditions were modified to avoid possible problems when an MCB
    is not tagged "correctly".}


  USES DOS;    {DOSVersion,Intr,Registers}

  CONST
    EnvironmentBlock:  STRING[12] = 'Environment ';
    ProgramBlock    :  STRING[12] = 'Program     ';

  TYPE
    MemoryControlBlock =     {MCB -- only needed fields are shown}
      RECORD
        Blocktag   :  BYTE;  {tag is M ($4D) except last is Z ($5A)}
        BlockOwner :  WORD;  {if nonzero, process identifier, usually PID}
        BlockSize  :  WORD;  {size in 16-byte paragraphs (excludes MCB)}
        misc       :  ARRAY[1..3] OF BYTE;  {placeholder}
        ProgramName:  ARRAY[1..8] OF CHAR   {only used by DOS 4.0; ASCIIZ}
      END;                   {PID normally taken from PSP}
    ProgramSegmentPrefix =   {PSP -- only needed fields are shown}
      RECORD                                           { offset }
        PSPtag     :  WORD;  { $20CD or $27CD if PSP}  { 00 $00 }
        misc       :  ARRAY[1..21] OF WORD;            { 02 $02 }
        Environment:  WORD                             { 44 $2C }
      END;

  VAR
    DOSVerNum:  BYTE;        {major version number, e.g., 3 for 3.X}
    LastSize :  WORD;        {used to detect multiple null MCBs}
    MCB      :  ^MemoryControlBlock;
    NullMCB  :  WORD;        {counter of MCBs pointing to 0-length blocks}
    r        :  Registers;   {TYPE defined in DOS unit}
    segment  :  WORD;
    vflag    :  BOOLEAN;     {Verify flag TRUE when /V specified}

  FUNCTION W2X(w:  WORD):  STRING; {binary word to hex character string}
    CONST HexDigit:  ARRAY[0..15] OF CHAR = '0123456789ABCDEF';
  BEGIN                 {similar to REXX standard D2X function}
    W2X :=  HexDigit[Hi(w) SHR 4] + HexDigit[Hi(w) AND $0F] +
            HexDigit[Lo(w) SHR 4] + HexDigit[Lo(w) AND $0F];
  END {W2X};  {change in CONST above suggested by Neil J. Rubenking}

  PROCEDURE ProcessMCB;                {Each Memory Control Block}
    VAR                                {is processed by this PROCEDURE.}
      b        :  CHAR;
      Blocktype:  STRING[12];
      bytes    :  LongInt;
      EnvSize  :  WORD;
      i        :  WORD;
      last     :  CHAR;
      MCBenv   :  ^MemoryControlBlock;
      MCBowner :  ^MemoryControlBlock;
      psp      :  ^ProgramSegmentPrefix;
  BEGIN
    IF   (MCB^.BlockTag <> $4D) AND (MCB^.BlockTag <> $5A) AND
         (MCB^.BlockTag <> $00)
    THEN BEGIN
      IF   NullMCB > 0
      THEN WRITELN (NullMCB:6,' contiguous MCBs pointing to empty ',
           'blocks not shown.');
      WRITELN ('Unknown Memory Control Block Tag ''',MCB^.BlockTag,
        '''.');
      WRITELN ('MemMap scan terminated.');
      HALT
    END;
    IF   (MCB^.BlockSize = 0) AND (LastSize = 0)
    THEN INC (NullMCB)  {Count but don't output multiple null MCBs}
    ELSE BEGIN
      LastSize := MCB^.BlockSize;
      IF   NullMCB > 0
      THEN BEGIN
        WRITELN (NullMCB:6,' contiguous MCBs pointing to empty ',
          'blocks not shown.');
        NullMCB := 0
      END
      ELSE BEGIN
        bytes := LongInt(MCB^.BlockSize) SHL 4; {size of MCB in bytes}
        WRITE (W2X(segment):6,W2X(MCB^.BlockSize):8,'0',bytes:9,
          W2X(MCB^.BlockOwner):8,'   ');

        IF   MCB^.BlockOwner = 0
        THEN WRITELN ('Free Space    <unallocated>')
        ELSE BEGIN
          psp := Ptr(MCB^.BlockOwner,0);            {possible PSP}
          {Almost all programs have a tag of $20CD; DOS MODE is one
           that uses $27CD in some versions.}
          IF   (psp^.PSPtag <> $20CD) AND (psp^.PSPtag <> $27CD)
          THEN WRITELN ('System        ', {not valid PSP}
                        '<DOS ',DosVerNum,'.',Hi(DOSVersion),' kernel>')
          ELSE BEGIN                      {valid program segment prefix}
            MCBenv := Ptr(psp^.Environment-1,0);    {MCB of environment}
            BlockType := 'Data        ';            {assume}
            IF   MCB^.Blockowner = (segment + 1)
            THEN BlockType := ProgramBlock
            ELSE
              IF   psp^.Environment = (segment + 1)
              THEN BlockType := EnvironmentBlock;
            WRITE (BlockType:12,'  ');
            IF  MCB^.BlockOwner <> MCBenv^.BlockOwner
            THEN
              IF   DOSVerNum <> 4
              THEN WRITELN ('<unknown>')  {different owner; unknown in 3.X}
              ELSE BEGIN                  {in DOS 4.0 short name is in MCB}
                MCBowner := Ptr(MCB^.Blockowner-1,0);    {MCB of owner block}
                i := 1;
                WHILE (MCBowner^.ProgramName[i] <> #$00) AND (i < 9) DO BEGIN
                  WRITE (MCBowner^.ProgramName[i]);
                  INC (i)
                END;
                WRITELN
              END
            ELSE BEGIN     {environment must have same owner as MCB}
              IF   DOSVerNum < 3
              THEN WRITELN ('<unknown>')       {DOS 1.X or 2.X}
              ELSE BEGIN                       {DOS 3.X}
                EnvSize := MCBenv^.BlockSize SHL 4;      {multiply by 16}
                i := 0;
                b := CHAR( Mem[psp^.Environment:i] );
                REPEAT
                  last := b;    {skip through ASCIIZ environment variables}
                  INC (i);
                  b := CHAR( Mem[psp^.Environment:i] );
                UNTIL (i > EnvSize) OR ( (b = #$00) AND (last = #$00));
                INC (i);        {end of environment block is $0000}
                b := CHAR( Mem[psp^.Environment:i] );
                IF   (i >= EnvSize) OR (b <> #$01)  {valid signature?}
                THEN WRITE ('<shell>')    {shell is probably COMMAND.COM}
                ELSE BEGIN
                  INC (i,2);              {skip process signature $0001}
                  b := CHAR( Mem[psp^.Environment:i] );
                  REPEAT
                    WRITE (b);            {output process name byte-by-byte}
                    INC (i);
                    b := CHAR( Mem[psp^.Environment:i] )
                  UNTIL (i > EnvSize) OR (b = #$00);
                END;
                WRITELN
              END
            END;

            IF   vflag AND (BlockType = EnvironmentBlock)
            THEN BEGIN                    {Display environment variables}
              i := 0;
              b := CHAR( Mem[psp^.Environment:i] );
              WRITELN;
              REPEAT
                IF   b = #$00
                THEN WRITELN              {end of ASCIIZ string}
                ELSE WRITE (b);
                last := b;
                INC (i);
                b := CHAR( Mem[psp^.Environment:i] );
              UNTIL (i > EnvSize) OR ( (b = #$00) AND (last = #$00));
              WRITELN
            END

          END
        END
      END
    END
  END {ProcessMCB};

BEGIN {MemMap}
   DOSVerNum := Lo(DOSVersion);   {major DOS version number, e.g., 3.X}
       {Note:  OS/2 1.1 DOS mode returns 10.10 for major/minor version}

   vflag := (ParamCount > 0) AND
            ((ParamStr(1) = '/v') OR (ParamStr(1) = '/V')) AND
            (DOSVerNum > 2);      {Ignore in DOS 2.X or lower}
   WRITELN ('Memory',' ':41,'MemMap (Version 2, May 89)');
   WRITELN ('Control    Block Size');
   WRITELN (' Block       [Bytes]       Owner');
   WRITELN ('Segment    hex   decimal  Segment      Type      ',
            '          Name');
   WRITELN ('-------  ------- -------  -------  ------------  ',
            '------------------------');
   LastSize := $FFFF;
   NullMCB := 0;

   r.AH := $52;    {undocumented DOS function that returns a pointer}
   Intr ($21,r);   {to the DOS 'list of lists'                      }
   segment := MemW[r.ES:r.BX-2];  {segment address of first MCB found at}
                                  {offset -2 from List of List pointer  }
   REPEAT
     MCB := Ptr(segment,0);       {MCB^ points to first MCB}
     ProcessMCB;                  {Look at each MCB}
     segment := segment + MCB^.BlockSize + 1
   UNTIL (MCB^.Blocktag = $5A)    {last one is $5A; all others are $4D}

END {MemMap}.
