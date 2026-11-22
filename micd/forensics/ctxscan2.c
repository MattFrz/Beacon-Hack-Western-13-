#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#define CHUNK 0x2000000ull
int main(int argc,char**argv){
    uint64_t start=strtoull(argv[1],0,0), end=strtoull(argv[2],0,0);
    int found=0;
    for(uint64_t a=start;a<end && found<20;a+=CHUNK){
        uint32_t*m=mmap(0,CHUNK,PROT_READ,MAP_SHARED|MAP_PHYS,NOFD,a);
        if(m==MAP_FAILED) continue;
        for(uint64_t o=0;o+64<=CHUNK;o+=16){
            uint32_t dw0=m[o/4], dw1=m[o/4+1], dw2=m[o/4+2], dw3=m[o/4+3];
            unsigned type=(dw0>>26)&0x1f;
            if(type==5 && dw3==0x10 && (dw2&1) &&
               ((dw1&0x7ff)==0xc00 || (dw1&0x7ff)==0x64)){
                unsigned state=dw0&7, itv=(dw0>>16)&0xff;
                printf("ISO-IN ctx @ 0x%llx: state=%u itv=%u maxp=%u burst=%u avgTRB=%u maxESIT=%u\n",
                    (unsigned long long)(a+o),state,itv,dw1&0x7ff,(dw1>>16)&0xff,
                    m[o/4+4]&0xffff,((m[o/4+4]>>16)<<16)|(m[o/4+5]&0xffff));
                printf("  dw: %08x %08x %08x %08x %08x %08x %08x %08x\n",
                    dw0,dw1,dw2,dw3,m[o/4+4],m[o/4+5],m[o/4+6],m[o/4+7]);
                found++;
            }
        }
        munmap(m,CHUNK);
    }
    printf("scan done, %d candidates\n",found);
    return 0;}
