#!/bin/bash

set -e

# get directory that the script exists in
cd "$( dirname "$0" )"

# get a list of amplipi's releases from github excluding those with a - in their name
releases=$(curl -s https://api.github.com/repos/micro-nova/amplipi/releases | jq -r '.[].tag_name' | grep -v -)

# download a relevant set of specs from amplipi's repo based on the releases list using git archive
for release in $releases; do
  # remove any existing release files
  if [[ ! -e "${release}.yaml" ]]; then
    # download the release
    wget https://raw.githubusercontent.com/micro-nova/AmpliPi/refs/tags/${release}/docs/amplipi_api.yaml -O ${release}.yaml
  fi
done
