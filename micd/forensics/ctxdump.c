#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#define RP1_OFF 0x1000000000ull
static void dump(uint64_t cpu_phys){
    uint8_t*p=mmap(0,0x1000,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,cpu_phys);
    if(p==MAP_FAILED){perror("mmap");return;}
    uint32_t*sc=(uint32_t*)p;
    printf("slotctx dw0=%08x (route %u, speed %u, ctx entries %u) dw2=%08x\n",
        sc[0],sc[0]&0xf,(sc[0]>>20)&0xf,(sc[0]>>27)+1,sc[2]);
    for(int dci=1;dci<=31;dci++){
        uint32_t*ec=(uint32_t*)(p+32+32*(dci-1));
        uint32_t dw0=ec[0],dw1=ec[1];
        unsigned state=dw0&7,mult=(dw0>>8)&3,itv=(dw0>>16)&0xff,cerr=(dw0>>24)&3,type=(dw0>>26)&0x1f;
        unsigned maxp=dw1&0x7ff,burst=(dw1>>16)&0xff;
        if(!state&&!type&&!maxp) continue;
        uint32_t avg=ec[4]&0xffff, esit=((ec[4]>>16)<<16)|(ec[5]&0xffff);
        const char*tn[]={"?","ISO-OUT","BULK-OUT","INT-OUT","CTRL","ISO-IN","BULK-IN","INT-IN"};
        printf("DCI %2u (%-7s): state=%u maxp=%u burst=%u mult=%u INTERVAL=%u (%u uf) cerr=%u avgTRB=%u maxESIT=%u\n",
            dci,tn[type<8?type:0],state,maxp,burst,mult,itv,1u<<itv,cerr,avg,esit);
        printf("           dw: %08x %08x %08x %08x %08x %08x\n",ec[0],ec[1],ec[2],ec[3],ec[4],ec[5]);
    }
}
int main(int argc,char**argv){
    /* argv[1]=DCBAAP (RP1 space); translate slot-1 ptr and dump */
    uint64_t dcbaap=strtoull(argv[1],0,0);
    uint64_t*w=mmap(0,0x1000,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,dcbaap-RP1_OFF);
    printf("DCBAA[0]=0x%llx [1]=0x%llx\n",(unsigned long long)w[0],(unsigned long long)w[1]);
    dump(w[1]-RP1_OFF);
    return 0;}
