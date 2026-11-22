#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#define RP1_OFF 0x1000000000ull
int main(int argc,char**argv){
    uint64_t base=strtoull(argv[1],0,0);
    volatile uint32_t*op=mmap(0,0x400,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,base+0x20);
    uint64_t dcbaap=((uint64_t)op[0x30/4+1]<<32)|op[0x30/4];
    uint64_t*d=mmap(0,0x1000,PROT_READ|PROT_WRITE|PROT_NOCACHE,MAP_SHARED|MAP_PHYS,NOFD,dcbaap-RP1_OFF);
    printf("ctrl 0x%llx DCBAAP=0x%llx\n",(unsigned long long)base,(unsigned long long)dcbaap);
    for(int s=0;s<64;s++) if(d[s]) printf("  slot %2d -> ctx 0x%llx (cpu 0x%llx)\n",s,
        (unsigned long long)d[s],(unsigned long long)(d[s]-RP1_OFF));
    return 0;}
