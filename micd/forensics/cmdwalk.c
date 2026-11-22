#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#define RP1_OFF 0x1000000000ull
int main(void){
    volatile uint32_t*cr=mmap(0,0x2000,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,0x1a5f000);
    if(cr==MAP_FAILED){printf("mmap failed\n");return 1;}
    int lastnz=-1;
    for(int i=0;i<256;i++){
        volatile uint32_t*t=cr+i*4;
        if(t[0]||t[1]||t[2]||t[3]){
            unsigned type=(t[3]>>10)&0x3f;
            printf("[%03d] +%03x: %08x %08x %08x %08x type=%u cyc=%u\n",
                i,i*16,t[0],t[1],t[2],t[3],type,t[3]&1);
            lastnz=i;
        }
    }
    printf("last nonzero TRB index=%d -> enqueue guess at +%03x\n",lastnz,(lastnz+1)*16);
    return 0;}
