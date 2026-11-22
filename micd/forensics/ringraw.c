#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#define RP1_OFF 0x1000000000ull
int main(int argc,char**argv){
    uint64_t r=strtoull(argv[1],0,0);
    volatile uint32_t*seg=mmap(0,0x2000,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,r);
    if(seg==MAP_FAILED){printf("mmap fail\n");return 1;}
    for(int i=0;i<12;i++){
        volatile uint32_t*t=seg+i*4;
        unsigned type=(t[3]>>10)&0x3f;
        printf("[%03d]: %08x %08x %08x %08x type=%u cyc=%u\n",i,t[0],t[1],t[2],t[3],type,t[3]&1);
    }
    int nz=0; for(int i=0;i<512;i++){volatile uint32_t*t=seg+i*4; if(t[0]||t[1]||t[2]||t[3])nz++;}
    printf("nonzero TRBs in 0x2000: %d\n",nz);
    for(int i=500;i<512;i++){volatile uint32_t*t=seg+i*4;
        unsigned type=(t[3]>>10)&0x3f;
        if(type==6) printf("link at %d: cyc=%u TC=%u\n",i,t[3]&1,(t[3]>>1)&1);}
    return 0;}
