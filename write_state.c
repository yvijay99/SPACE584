#include "write_state.h"
#include <stdio.h>

void write_state(int state)
{
    FILE *f;
    f = fopen("/tmp/adcs_state.bin", "wb");
    if (f != NULL) {
        fwrite(&state, sizeof(int), 1, f);
        fclose(f);
    }
}