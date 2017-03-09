#include <zlib.h>

#include <stdio.h>


int main(int argc, char **argv) {
    printf("zlib %s\n", zlibVersion());
    return 0;
}
