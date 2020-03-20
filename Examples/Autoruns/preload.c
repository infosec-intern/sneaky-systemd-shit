#include <stdio.h>

/*
    This is NOT MY CODE
    Code borrowed from @ForensicITGuy's libpreloadvaccine project
    Source: https://github.com/ForensicITGuy/libpreloadvaccine/blob/master/test/test_data/preload.c
*/

static void init(int argc, char **argv, char **envp) {
    printf("Preload Successful!\n");
}

__attribute__((section(".init_array"), used)) static typeof(init) *init_p = init;