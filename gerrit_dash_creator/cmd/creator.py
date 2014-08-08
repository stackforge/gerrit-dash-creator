#!/usr/bin/env python
#
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

import argparse
import os
import os.path
import sys
import urllib

import jinja2
from pkg_resources import resource_filename
from six.moves import configparser
import six


def escape_comma(buff):
    """Because otherwise Firefox is a sad panda."""
    return buff.replace(',', '%2c')


def generate_dashboard_url(dashboard):
    """Generate a dashboard URL from a given definition."""
    try:
        title = dashboard.get('dashboard', 'title')
    except configparser.NoOptionError:
        raise ValueError("option 'title' in section 'dashboard' not set")

    try:
        foreach = escape_comma(dashboard.get('dashboard', 'foreach'))
    except configparser.NoOptionError:
        raise ValueError("option 'foreach' in section 'dashboard' not set")

    try:
        baseurl = dashboard.get('dashboard', 'baseurl')
    except configparser.NoOptionError:
        baseurl = 'https://review.openstack.org/#/dashboard/?'

    url = baseurl
    url += urllib.urlencode({'title': title, 'foreach': foreach})
    url += '&'
    for section in dashboard.sections():
        if not section.startswith('section'):
            continue

        try:
            query = dashboard.get(section, 'query')
        except configparser.NoOptionError:
            raise ValueError("option 'query' in '%s' not set" % section)

        title = section[9:-1]
        encoded = urllib.urlencode({title: query})
        url += "&%s" % encoded
    return url


def get_options():
    """Parse command line arguments and options."""
    parser = argparse.ArgumentParser(
        description='Create a Gerrit dashboard URL from specified dashboard '
                    'definition files')
    parser.add_argument('dashboard_files', nargs='+',
                        metavar='dashboard_file',
                        help='Dashboard definition file to create URL from')
    parser.add_argument('--template', default='single.txt',
                        help='Name of template')
    parser.add_argument('--template-path',
                        default=resource_filename(__name__, "../../templates"),
                        help='Path to scan for template files')
    parser.add_argument('--template-file', default=None,
                        help='Location of a specific template file')
    return parser.parse_args()


def read_dashboard_file(fname):
    """Read and parse a dashboard definition from a specified file."""
    dashboard = configparser.ConfigParser()
    dashboard.readfp(open(fname))
    return dashboard


def load_template(template, template_path):
    #loader = jinja2.PackageLoader('gerrit_dash_creator')

    try:
        loader = jinja2.FileSystemLoader(template_path)
        environment = jinja2.Environment(loader=loader)
        template = environment.get_template(template)
    except (jinja2.exceptions.TemplateError, IOError) as e:
        print("error: opening template '%s' failed: %s" %
              (template, e.__class__.__name__))
        return
    return template


def get_template(template_file=None, template_path=None, template_name=None):
    if template_file:
        template = load_template(
            os.path.basename(template_file),
            os.path.dirname(os.path.abspath(template_file))
        )
    else:
        template = load_template(template, template_path)

    return template


def get_configuration(dashboard):
    configuration = six.StringIO()
    dashboard.write(configuration)
    result = configuration.getvalue()
    configuration.close()
    return result


def main():
    """Entrypoint."""
    result = 0
    opts = get_options()

    template = get_template(
        template_file=opts.template_file,
        template_path=opts.template_path,
        template_name=opts.template
    )

    if not template:
        return 1

    for dashboard_file in opts.dashboard_files:
        if (not os.path.isfile(dashboard_file) or
                not os.access(dashboard_file, os.R_OK)):
            print("\nerror: dashboard file '%s' is missing or is not readable" %
                  dashboard_file)
            result = 1
            continue

        try:
            dashboard = read_dashboard_file(dashboard_file)
        except configparser.Error as e:
            print("\nerror: dashboard file '%s' cannot be parsed\n\n%s" %
                  (dashboard_file, e))
            return 1
            continue

        try:
            url = generate_dashboard_url(dashboard)
        except ValueError as e:
            print("\nerror:\tgenerating dashboard '%s' failed\n\t%s" %
                  (dashboard_file, e))
            result = 1
            continue

        variables = {
            'title': dashboard.get('dashboard', 'title') or None,
            'description': dashboard.get('dashboard', 'description') or None,
            'url': url,
            'filename': dashboard_file,
            'configuration': get_configuration(dashboard)
        }
        print(template.render(variables))

    return result


if __name__ == '__main__':
    sys.exit(main())
