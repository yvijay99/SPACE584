#include <sys/time.h>

void get_unix_time_wrapper(double *t_unix)
{
    struct timeval tv;
    gettimeofday(&tv, NULL);
    *t_unix = (double)tv.tv_sec + (double)tv.tv_usec * 1e-6;
}