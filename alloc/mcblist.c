/*
  ====================  MCB.C  =======================================
    This program chains through all the DOS memory control
    blocks and computes and prints out information related to
    each one.
    R.J. Moore (C) 06 June 1988 Version 1.2. May be used freely
    for non-commercial purposes only.
    Compiled under Turbo C, Version 1.5, using the small memory
    model, which itated the explicit declaration of some huge and
    far pointers.  Tested on IBM PC, IBM XT, IBM AT, TP/286 AT
    clone, under PC-DOS 2.1, 3.1, 3.2, and 3.3.  Also run under
    MS-DOS 2.11 on a DEC Rainbow.  PC-DOS 3.3 required some
    adjustments as discussed in later comments.
    ==================================================================
*/

#include <stdio.h>
#include <dos.h>

/*-------Global declarations----------------------------------------*/
struct MCB /*template for a one paragraph MS-DOS MCB    */
{
    char chain;      /* 'Z' for last MCB, 'M' for all others      */
    unsigned pid;    /* PSP segment for process owning the MCB    */
    unsigned psize;  /* Paragraphs of memory in the MB following  */
    char unused[11]; /* Last 11 bytes of MCB (currently unused)   */
};

typedef struct MCB huge *PTRMCB; /*PTRMCB is a type declared
                                   to be a huge pointer to MCB   */

/*-------Function prototypes----------------------------------------*/
void main(void);
void far *ffmcb(void);   /* Returns far pointer to first MCB.      */
void prn_header(void);   /* Prints output table header.            */
void prn_mcb(PTRMCB pm); /* Prints out MCB and related information.*/
                         /* Prints out owner name string for pid.  */
void prn_pid_own(unsigned pid, unsigned parent);

/*------main()------------------------------------------------------*/
/* Executive to control finding a pointer to each MCB and directing
   the printing out of information for each until the end of the
   MCB chain is reached.                                            */

void main()
{
    PTRMCB ptrmcb; /* ptrmcb is a huge pointer to an MCB  */

    /* Get pointer to first MCB. Note that ffmcb() returns a far
       pointer, which is then cast to a huge pointer. A far pointer
       is good enough to find the first MCB since a far pointer can
       start at any memory location.  However, the use of this pointer
       in ptrmcb must be huge because MCBs range over more than 64K,
       which is all that a far pointer can handle since the segment
       portion of a far pointer never changes. I, of course, found
       this out the hard way.  Such special declarations can be
       avoided if this program is compiled under the huge memory
       model, but I think the method I used is more instructive.     */

    ptrmcb = (PTRMCB)ffmcb(); /* Get far pointer to first MCB and
                                 cast to huge pointer via (PTRMCB).  */
    prn_header();             /* Print out table header to stdout.   */
    prn_mcb(ptrmcb);          /* Print out information for first MCB.*/

    /* Print out MCB information for each of the remaining MCBs    */
    do
    {
        ptrmcb += ptrmcb->psize + 1; /* Get pointer to next MCB       */

        /* Each unit increment of ptrmcb corresponds to one paragraph;
           adding ptrmcb->psize thus increments through entire allocated
           memory block following the MCB. Since this doesn't include
           space occupied by the MCB itself, must increment through one
           more paragraph (+ 1) to point to the next MCB.               */

        prn_mcb(ptrmcb); /* Print out information for MCB */
    } while (ptrmcb->chain == 'M'); /* as long as not at end of chain*/
    /*Print out final decoration.    */
    printf("========================================================");
    puts("===========");
}

/*------ffmcb()-----------------------------------------------------*/
/* Returns a far pointer to the first MCB in memory.  Explict
   declaration of far needed since small model was used to compile,
   as noted in a comment in main.                                   */

void far *ffmcb(void)
{
    union REGS regs; /* REGS and SREGS defined in dos.h.       */
    struct SREGS sregs;
    unsigned far *segmptr;         /*  Far pointer to segment address of MCB.*/
    regs.h.ah = 0x52;              /*  Undocumented MS-DOS function 52H.     */
    intdosx(&regs, &regs, &sregs); /* ES:BX-2 points to segment
                                      address of first MCB on return
                                      and is copied to segmptr below.*/
    segmptr = MK_FP(sregs.es, regs.x.bx - 2);
    return MK_FP(*segmptr, 0); /* Return pointer to MCB itself.  */
} /* Segment pointed to by *segmptr.*/
/* Offset is zero (on paragraph). */

/*-----------prn_header()-------------------------------------------*/
/* Prints out header for the output variables describing the
   information for each MCB which will be subsequently printed
   out by the function prn_mcb().
*/
void prn_header(void)
{
    printf("===================================================");
    puts("================");
    puts("MCB MCB  ID PID      MB PAR- ENV  OWNER");
    puts("NO. SEG            SIZE ENT  BLK?");
    printf("===================================================");
    puts("================");

    /*    MCB NO. = ordinal number of MCB being processed (1,2,...).
          MCB SEG = segment address (hex) of memory control block.
          ID      = chain id, 'Z' if last MCB, 'M' otherwise.
          PID     = process id, the PSP segment address (hex) of owner of
                    the MCB. (PSP always starts on paragraph boundary.)
          MB SIZE = size of the allocated memory block controlled by
                    the MCB (the MB immediately follows its associated
                    MCB at the next paragraph in memory (decimal bytes).
          PARENT  = segment address (hex) of parent process's PID.
          ENV BLK?= 'Y' if the MCB controls an environment block,
                    'N' otherwise.
          OWNER   = string that prints out program associated with
                    the PID.
    */
}

/*------prn_mcb()---------------------------------------------------*/
/* Prints out the information associated with the MCB pointer passed
   to it in its argument list
*/

void prn_mcb(PTRMCB pm)
{
    static cnt = 0;    /* Count of number of times parent has
                          been equal to the pid.                */
    static mcbnum = 1; /* Ordinal # of MCB being printed out.   */
    unsigned parid;    /* Parent id (segment address of parent
                           process).                            */
    unsigned mcbseg;   /* Segment address of MCB (offset is
                           always zero since paragraph aligned).*/
    char envf;         /*Set to 'Y'/'N' if MB is/is not an
                           environment block.                   */
    unsigned envseg;   /*Segment address of pid's environment
                           block.                               */

    /* Get parent id located at pid:16H                              */
    parid = *(unsigned far *)MK_FP(pm->pid, 0x16);

    mcbseg = FP_SEG(pm); /* Segment address of the MCB            */

    envseg = *(unsigned far *)MK_FP(pm->pid, 0x2C); /* segment      */
                                                    /* Address of pid's environment          */
                                                    /* located at pid:2CH.                   */

    /* If the MCB segment value plus one equals the environment
       segment address, then the MCB controls the environment
       block (set envf = 'Y'); otherwise set envf = 'N'             */

    envf = mcbseg + 1 == envseg ? 'Y' : 'N';

    /* Count the number of times parent and pid have been equal
       (when this is true, memory blocks are owned by COMMAND.COM   */

    if (parid == pm->pid)
        cnt++;

    /* The above determination of whether an MB is an environment
       block isn't complete for DOS versions 2.0 thru 3.2.  The
       above logic will not identify the master environment block
       owned by the master copy of COMMAND.COM since the value at
       pid:2CH contains zero, not the segment address of the master
       environment.  The logic below uses the fact that the master
       environment follows the master COMMAND.COM in memory. (The
       environment copies for other programs are in memory BEFORE
       the pid they are associated with.) Starting with DOS 3.3
       pid:2CH always points to the environment, even for the
       master COMMAND.COM, so the following is not needed (but it
       doesn't do any harm).                                         */

    if (!envseg && cnt == 2)
        envf = 'Y';

    /* Print out MCB information except for owner name in the
       following call to printf().                                  */

    printf("%2.2u%06.4X%2.1c%06.4X%7lu%5.4X %-5.1c",
           mcbnum++, mcbseg, pm->chain, pm->pid, (long)pm->psize * 16, parid, envf);

    /* Call prn_pid_own() to find and print out owner string            */

    prn_pid_own(pm->pid, parid);
}

/*------prn_pid_own()-----------------------------------------------*/
/* Prints out owner name string associated with the pid, which is an
   input parameter.  Also needs the parent address as an input to
   identify cases where COMMAND.COM is the owner (true when
   pid=parent). This function also uses the fact that the following
   pid values are special:

   pid = 0 means that MCB is a free block of memory
   pid = 8 means that the MCB is owned by IBMDOS.COM/MSDOS.SYS
   pid = parent means that the MCB is owned by COMMAND.COM (the only
         program that is its own parent.)

   In these cases I assign appropriate owner string names instead of
   getting them from the environment since they are not available
   there.  Owner names consisting of a string with the drive, path,
   and file name of the program that owns the memory are only
   available in DOS 3.x. Note that DOS 3.3 does not provide an owner
   string for the master copy of COMMAND.COM for some reason.  This
   is of no consequence in the method used here.
*/

void prn_pid_own(unsigned pid, unsigned parent)
{
    unsigned far *envsegptr;  /* Pointer to seg address of environment*/
    char far *envptr;         /* Pointer to pid's environment         */
    unsigned far *envsizeptr; /* Pointer to envsize word below        */
    unsigned envsize;         /* Size of pid's environment            */

    /* Ordinal # of copy of COMMAND.COM in memory (ccnum=1 for master
       copy, 2 for first secondary copy (if any), etc.                */

    static unsigned char ccnum = 0;

    /* Pid value saved from previous call to this function.
    Initialized to an impossible value (no PSP could start at FFFF:0) */

    static prev_pid = 0xFFFF;

    switch (pid)
    {
        /* Assign owner names for two special cases                  */
    case 0:
        puts("FREE MEMORY CONTROL BLOCK");
        return;
    case 8:
        puts("IBMDOS.COM/MSDOS.SYS");
        return;
    }

    /* pid:2CH contains ptr to segment address of pid's environment   */
    envsegptr = (unsigned far *)MK_FP(pid, 0x2C);

    /* Get pointer to the environment block itself                    */
    envptr = (char far *)MK_FP(*envsegptr, 0);

    /* Define a pointer that contains the size of the environment
       block. Must point back one paragraph (where the environment's
       MCB resides) plus three bytes forward (where the MCB block
       size field is).                                                */
    envsizeptr = (unsigned far *)MK_FP(*envsegptr - 1, 0x3);

    /* Get the size of the environment using the above pointer in
       units of bytes (1 paragraph = 16 decimal bytes).               */
    envsize = *envsizeptr * 16;

    /* If next stmt is satisfied, owner is a copy of COMMAND.COM    */

    if (pid == parent)
    {
        /* If previous pid is different from current pid, have found a
           new secondary copy of COMMAND - ccnum keeps track records the
           copy number.                                                 */

        if (prev_pid != pid)
            ccnum++;
        printf("COMMAND.COM COPY #%-2u\n", ccnum);

        prev_pid = pid; /* Save current pid - will be previous   */
        return;         /*  in the next call to this function    */
    }

    /* Loop at most until the end of the environment                  */

    while (envsize)
    {
        /* Decrement counter (envsize) indicating # of bytes left in
           environment and advance pointer thru environment block until
           either end of environment or a NULL is located
        */
        while (--envsize && *envptr++)
            ;

        /* The next stmt will be true if another NULL immediately
           follows the first one located and a word count of 0001 then
           follows that.                                              */

        if (!*envptr && *(unsigned far *)(envptr + 1) == 0x1)
        {
            envptr += 3; /* Correct pattern found (00 00 01 00) */
            break;       /* so point envptr to owner string     */
        }
    }

    if (envsize)
    {
        /* If an owner string was found before the end of the
            environment so print out the owner name.  Note that can't
            use puts() or printf() to print out the results since I
            used the small memory model.
         */
        while (*envptr)
            putchar(*envptr++);
        putchar('\n');
    }
    else
        /* If reached the end of the environment without finding
           an owner string (should only occur for DOS 2.x)             */
        puts("UNKNOWN OWNER");
}
