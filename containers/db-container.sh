#! /bin/sh -e

# Find path to containers directory.
containers=$(dirname $0)

# Create mariadb state directory if it does not exist.
mkdir -p $containers/mariadb-state

# Build the container.
guix system container --network \
     --share=$containers/mariadb-state=/var/lib/mysql \
     $containers/db-container.scm
