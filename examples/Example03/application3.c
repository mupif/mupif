#include <stdio.h>
#include <stdlib.h>

int main () {
  FILE *in, *out;
  double value, sum = 0.0;
  int count = 0;

  if ((in = fopen ("app3.in", "r")) != NULL) {
    while (fscanf(in, "%le", &value) != EOF) {
      sum += value;
      count++;
    }
    
    fclose (in);
    if ((out = fopen ("app3.out", "w")) != NULL) {

      fprintf (out, "%le", sum/count);
    } else {
      fprintf (stderr, "Failed to open output file\n");
      exit(2);
    }

    fclose (out);
    return 1;

  } else {
    fprintf (stderr, "Failed to open intput file\n");
    exit(2);
  }
  



}
