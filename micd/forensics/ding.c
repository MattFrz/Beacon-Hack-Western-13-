#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#define RP1_OFF 0x1000000000ull
int main(int argc,char**argv){
    uint64_t base=strtoull(argv[1],0,0);
    int slot=atoi(argv[2]), dci=atoi(argv[3]);
    volatile uint32_t*cap=mmap(0,0x40,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,base);
    uint32_t dboff=cap[0x14/4];
    volatile uint32_t*op=mmap(0,0x400,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,base+0x20);
    uint64_t dcbaap=((uint64_t)op[0x30/4+1]<<32)|op[0x30/4];
    uint64_t*d=mmap(0,0x1000,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,dcbaap-RP1_OFF);
    volatile uint32_t*db=mmap(0,0x1000,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,base+dboff);
    printf("dboff=0x%x slot1 ctx=0x%llx\n",dboff,(unsigned long long)d[1]);
    volatile uint32_t*ctx=mmap(0,0x1000,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,d[slot]-RP1_OFF);
    volatile uint32_t*ec=(volatile uint32_t*)((uint8_t*)ctx+64+64*(dci-1));
    printf("before: dw0=%08x dequeue=%08x\n",ec[0],ec[2]);
    db[slot]=dci;   /* ring doorbell for slot, target DCI */
    printf("rang doorbell slot %d target DCI %d\n",slot,dci);
    for(int i=0;i<5;i++){ sleep(2);
        printf("t+%ds: dw0=%08x dequeue=%08x\n",(i+1)*2,ec[0],ec[2]); }
    return 0;}
