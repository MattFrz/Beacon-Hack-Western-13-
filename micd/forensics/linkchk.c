#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#define RP1_OFF 0x1000000000ull
static volatile uint32_t*mp(uint64_t p,size_t l){
    volatile uint32_t*m=mmap(0,l,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,p);
    if(m==MAP_FAILED){printf("mmap 0x%llx FAIL\n",(unsigned long long)p);exit(1);}
    return m;}
int main(int argc,char**argv){
    uint64_t base=strtoull(argv[1],0,0);
    volatile uint32_t*op=mp(base+0x20,0x400);
    uint64_t dcbaap=((uint64_t)op[0x30/4+1]<<32)|op[0x30/4];
    volatile uint64_t*d=(volatile uint64_t*)mp(dcbaap-RP1_OFF,0x1000);
    /* walk ALL slots; find the one whose EP13-ish iso ctx matches the C270 */
    for(int s=1;s<=8;s++){
        if(!d[s]) continue;
        volatile uint32_t*ctx=(volatile uint32_t*)mp(d[s]-RP1_OFF,0x1000);
        printf("slot %d: slotctx dw0=%08x\n",s,ctx[0]);
        for(int dci=3;dci<=15;dci+=2){
            volatile uint32_t*ec=(volatile uint32_t*)((uint8_t*)ctx+64+64*(dci-1));
            uint32_t mps=(ec[1]>>16)&0xffff;
            if(mps==100||mps==1020){   /* C270 audio or video in driver layout */
                uint64_t ring=((((uint64_t)ec[3])<<32)|(ec[2]&0xfffffff0ull))-RP1_OFF;
                printf("  DCI %d: state=%u itv=%u mps=%u ring CPU=0x%llx\n",
                    dci,ec[0]&7,(ec[0]>>16)&0xff,mps,(unsigned long long)ring);
                volatile uint32_t*tr=mp(ring&~0xfffull,0x2000);
                for(int i=0;i<256;i++){
                    volatile uint32_t*t=tr+(ring&0xfffull)/16+i*4;
                    if(((t[3]>>10)&0x3f)==6){
                        printf("  LINK TRB at idx %d: %08x %08x %08x %08x  cyc=%u TC=%u\n",
                            i,t[0],t[1],t[2],t[3],t[3]&1,(t[3]>>1)&1);
                        printf("  first data TRB: %08x %08x %08x %08x cyc=%u\n",
                            tr[(ring&0xfffull)/16+0],tr[(ring&0xfffull)/16+1],
                            tr[(ring&0xfffull)/16+2],tr[(ring&0xfffull)/16+3],
                            tr[(ring&0xfffull)/16+3]&1);
                        break;
                    }
                }
            }
        }
    }
    return 0;}
