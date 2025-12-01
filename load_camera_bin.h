#ifndef LOAD_CAMERA_BIN_H
#define LOAD_CAMERA_BIN_H

void load_camera_bin(const char *path_st, const char *path_ss,
                     double *phi_st, double *t_st, int *valid_st,
                     double *phi_ss, double *t_ss, int *valid_ss);

#endif