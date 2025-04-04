// main: Project entry point, allows launching client or server based on Command Line Arguments.
#include <stdlib.h>
#include <stdio.h>

#include "interface.h"


int main(int argc, char ** argv){

    print_commands();

    interface();


    return EXIT_SUCCESS;
}