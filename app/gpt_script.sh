#!/bin/bash

# Loop through each line in the input (paths)
while read -r path; do
  echo "#------ $path -------" # Print the header with the file name
  cat "$path"     # Display the contents of the file
  echo -e "\n"    # Print a newline character for spacing
done < "${1:-/dev/stdin}" # Read from a file if provided, otherwise from standard input
