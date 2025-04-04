#ifndef INTERFACE_H
#define INTERFACE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>   // for getcwd() and chdir()
#include <limits.h>   // for PATH_MAX
#include <errno.h>

void print_commands();
int interface();
char *trim_whitespace(char *str);
void exec_cd(char *input);

#endif // INTERFACE_H
