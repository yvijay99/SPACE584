#include <stdio.h>

void load_camera_bin(const char *path_st, const char *path_ss,
                     double *phi_st, double *t_st, int *valid_st,
                     double *phi_ss, double *t_ss, int *valid_ss)
{
    FILE *f;
    
    /* Read star tracker */
    *valid_st = 0;
    *phi_st = 0.0;
    *t_st = 0.0;
    
    f = fopen(path_st, "rb");
    if (f != NULL) {
        if (fread(phi_st, sizeof(double), 1, f) == 1 &&
            fread(t_st, sizeof(double), 1, f) == 1) {
            *valid_st = 1;
        }
        fclose(f);
    }
    
    /* Read sun sensor */
    *valid_ss = 0;
    *phi_ss = 0.0;
    *t_ss = 0.0;
    
    f = fopen(path_ss, "rb");
    if (f != NULL) {
        if (fread(phi_ss, sizeof(double), 1, f) == 1 &&
            fread(t_ss, sizeof(double), 1, f) == 1) {
            *valid_ss = 1;
        }
        fclose(f);
    }
}