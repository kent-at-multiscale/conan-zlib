#include <zlib.h>

#include <iostream>
#include <string>


int main(int argc, char **argv) {
    std::cout << "zlib " << zlibVersion() << std::endl;
    return 0;
}
