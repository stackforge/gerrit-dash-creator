#!/bin/sh

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

output_directory=doc/dashboards/
mkdir -p $output_directory
cp doc/source/conf.py $output_directory
cp doc/source/usage.rst $output_directory
cp doc/source/installation.rst $output_directory
echo ".. include:: ../../README.rst" > $output_directory/readme.rst
echo ".. include:: ../../CONTRIBUTING.rst" > $output_directory/contributing.rst

for dashboard in $(find dashboards -name '*.dash' | sort); do
  output=$(basename $dashboard .rst)
  python gerrit_dash_creator/cmd/creator.py --template-directory templates --template single.rst $dashboard > $output_directory/dashboard_$output.rst
done

echo "OpenStack Gerrit Dashboards" >> $output_directory/index.rst
echo "===========================" >> $output_directory/index.rst
echo >> $output_directory/index.rst
echo ".. toctree::" >> $output_directory/index.rst
echo >> $output_directory/index.rst
echo "   readme" >> $output_directory/index.rst
echo "   installation" >> $output_directory/index.rst
echo "   usage" >> $output_directory/index.rst
echo "   contributing" >> $output_directory/index.rst

for dashboard in $(find $output_directory -name 'dashboard_*.rst' | sort); do
  dashboard=$(basename $dashboard .rst)
  echo "  " $dashboard >> $output_directory/index.rst
done
