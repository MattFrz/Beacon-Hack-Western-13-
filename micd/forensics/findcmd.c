#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#define RP1_OFF 0x1000000000ull
#define CHUNK 0x2000000ull
int main(int argc,char**argv){
    uint64_t start=strtoull(argv[1],0,0), end=strtoull(argv[2],0,0);
    int found=0;
    for(uint64_t a=start;a<end && found<6;a+=CHUNK){
        uint32_t*m=mmap(0,CHUNK,PROT_READ,MAP_SHARED|MAP_PHYS,NOFD,a);
        if(m==MAP_FAILED) continue;
        for(uint64_t o=0;o+16<=CHUNK;o+=16){
            uint32_t dw3=m[o/4+3], dw2=m[o/4+2], dw0=m[o/4], dw1=m[o/4+1];
            unsigned type=(dw3>>10)&0x3f, slot=(dw3>>24)&0x1f;
            if(type==12 && slot>=1 && slot<=15 && dw2==0 && (dw0&0x3f)==0 &&
               (dw1==0x10||dw1==0)){
                uint64_t ip=((uint64_t)dw1<<32)|dw0;
                printf("CFG-EP TRB @0x%llx: input ctx RP1=0x%llx cyc=%u\n",
                    (unsigned long long)(a+o),(unsigned long long)ip,dw3&1);
                volatile uint32_t*ic=mmap(0,0x1000,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,ip-RP1_OFF);
                if(ic!=MAP_FAILED){
                    printf("  A/D add=%08x drop=%08x slot dw0=%08x\n",ic[0],ic[1],ic[2]);
                    volatile uint32_t*ep13=(volatile uint32_t*)((uint8_t*)ic+8+64+64*12);
                    printf("  input EP13: dw0=%08x (type=%u itv=%u) dw1=%08x dw2=%08x dw3=%08x\n",
                        ep13[0],(ep13[0]>>26)&0x1f,(ep13[0]>>16)&0xff,ep13[1],ep13[2],ep13[3]);
                }
                found++;
            }
        }
        munmap(m,CHUNK);
    }
    printf("done %d\n",found);
    return 0;}
