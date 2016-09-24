import io
import os
import zipfile
import time

import click
import ConfigParser
import requests


# Lokalise API Endpoints
LIST_LANGUAGES = 'https://lokalise.co/api/language/list?api_token={0}&id={1}'
EXPORT = 'https://lokalise.co/api/project/export'
IMPORT = 'https://lokalise.co/api/project/import'
EMPTY = 'https://lokalise.co/api/project/empty'
SNAPSHOT = 'https://lokalise.co/api/project/snapshot'

class Resource(object):
    file_format = ''
    languages = []
    files_name = ''
    files_dir = ''
    files_dir_map = {}


class Context(object):
    api_token = ''
    project_id = ''
    resources = {}

    def __init__(self):
        parser = ConfigParser.ConfigParser()
        parser.read('.ilseconfig')

        try:
            self.api_token = parser.get('ilse', 'API_TOKEN')
        except ConfigParser.Error:
            click.echo("Missing API_TOKEN!")
            raise click.Abort

        try:
            self.project_id = parser.get('ilse', 'PROJECT_ID')
        except ConfigParser.Error:
            click.echo("Missing PROJECT_ID!")
            raise click.Abort

        for section in parser.sections():
            if section == 'ilse':
                continue

            res = Resource()

            try:
                res.file_format = parser.get(section, 'FORMAT')
            except ConfigParser.Error:
                click.echo("Missing FORMAT for Resource {0}".format(section))
                raise click.Abort

            try:
                res.languages = parser.get(section, 'LANGUAGES').split(',')
            except ConfigParser.Error:
                click.echo("Missing LANGUAGES for Resource {0}"
                           .format(section))
                raise click.Abort

            try:
                res.files_dir = parser.get(section, 'FILES_DIR')
            except ConfigParser.Error:
                click.echo("Missing FILES_DIR for Resource {0}".format(section))
                raise click.Abort

            try:
                res.files_name = parser.get(section, 'FILES_NAME')
            except ConfigParser.Error:
                click.echo("Missing FILES_NAME for Resource {0}".format(section))
                raise click.Abort

            res.files_dir_map = {}
            if parser.has_option(section, 'FILES_DIR_MAP'):
                for fdm in parser.get(section, 'FILES_DIR_MAP').split(','):
                    fdm_kv = fdm.split(':')
                    res.files_dir_map[fdm_kv[0]] = fdm_kv[1]

            self.resources[section] = res


pass_ctx = click.make_pass_decorator(Context, ensure=True)


@click.group()
@pass_ctx
def cli(ctx):
    pass


@cli.command()
@pass_ctx
def debug_config(ctx):
    click.echo('API_TOKEN: %s' % ctx.api_token)
    click.echo('PROJECT_ID: %s' % ctx.project_id)
    for name, resource in ctx.resources.iteritems():
        click.echo('RESOURCES: %s' % resource.file_format)
        click.echo('  LANGUAGES: %s' % resource.languages)
        click.echo('  FILES_NAME: %s' % resource.files_name)
        click.echo('  FILES_DIR: %s' % resource.files_dir)
        click.echo('  FILES_DIR_MAP: %s' % resource.files_dir_map)


@cli.command()
@pass_ctx
def language(ctx):
    response = requests.get(LIST_LANGUAGES.format(ctx.api_token,
                                                  ctx.project_id))
    languages = response.json()['languages']
    for l in languages:
        click.echo("ISO: %s" % l['iso'])
        click.echo("Name: %s" % l['name'])
        click.echo("Words: %s" % l['words'])
        click.echo("Right-to-Left: %s" % ('Y' if l['rtl'] == '1' else 'N'))
        click.echo("Default: %s" % ('Y' if l['is_default'] == '1' else 'N'))
        click.echo("")


@cli.command()
@click.option('--resource', '-r')
@click.option('--language', '-l')
@pass_ctx
def pull(ctx, resource, language):
    resources = [resource] if resource else ctx.resources.keys()
    for r in resources:
        res = ctx.resources[r]
        if not res:
            continue
        if r == 'stringsdict':
            continue

        languages = [str(language)] if language else res.languages

        params = {}
        params['api_token'] = ctx.api_token
        params['id'] = ctx.project_id
        params['type'] = res.file_format
        params['bundle_filename'] = "%PROJECT_NAME%-Locale.zip"
        params['bundle_structure'] = "%LANG_ISO%/" + res.files_name
        params['langs'] = str(languages)

        click.echo("Requesting bundle...")
        click.echo(params)
        resp = requests.post(EXPORT, data=params)
        if resp.status_code != 200:
            click.echo("Something went wrong when requesting bundle "
                       "(error: {0})!".format(resp.status_code))
            return

        click.echo(resp.json())
        download_path = resp.json()['bundle']['file']
        download_url = 'https://lokalise.co/%s' % download_path
        click.echo("Downloading bundle from %s..." % download_url)
        fresp = requests.get(download_url)
        if fresp.status_code != 200:
            click.echo("Something went wrong when downloading bundle "
                       "(error: {0})!".format(fresp.status_code))

        with zipfile.ZipFile(io.BytesIO(fresp.content)) as z:
            dest = 'ilsetmp{0}'.format(int(time.time()))
            click.echo("Extracting bundle to {0}".format(dest))
            z.extractall(dest)
            for lang_code in languages:
                files_lang_code = res.files_dir_map.get(lang_code, lang_code)

                dest_dir = res.files_dir.replace('%LANG_ISO%', files_lang_code)
                click.echo("Copying {0} files".format(lang_code))
                os.system("find {0} -name \'{1}\' -maxdepth 1"
                          " -exec bash -c \'"
                          " cp $1/* \"{2}\""
                          " \' -- {{}} \;".format(dest, lang_code, dest_dir))

            os.system("rm -r {0}".format(dest))


@cli.command()
@click.option('--resource', '-r')
@click.option('--language', '-l')
@click.option('--replace', is_flag=True)
@click.option('--fill_empty', is_flag=True)
@click.option('--distinguish', is_flag=True)
@click.option('--hidden', is_flag=True)
@click.option('--overwrite', is_flag=True)
@click.option('--snapshot', is_flag=True)
@pass_ctx
def push(ctx, resource, language, replace, fill_empty, distinguish, hidden, overwrite, snapshot):
    resources = [resource] if resource else ctx.resources.keys()

    if snapshot or overwrite:
        click.echo("Taking snapshot of the project...")
        params = {}
        params['api_token'] = ctx.api_token
        params['id'] = ctx.project_id
        resp = requests.post(SNAPSHOT, data=params)
        if resp.status_code != 200:
            click.echo("Something went wrong when taking project snapshot! "
                       "(error:{0})!".format(resp.status_code))
            return

    if overwrite:
        snapshot = True
        click.echo("Overwriting project...")
        params = {}
        params['api_token'] = ctx.api_token
        params['id'] = ctx.project_id
        resp = requests.post(EMPTY, data=params)
        if resp.status_code != 200:
            click.echo("Something went wrong when overwriting project! "
                       "(error:{0})!".format(resp.status_code))
            return

    for r in resources:
        res = ctx.resources[r]
        if not res:
            continue

        languages = [language] if language else res.languages
        files = [res.files_name.replace('%FORMAT%', res.file_format)]

        for l in languages:
            params = {}
            params['api_token'] = ctx.api_token
            params['id'] = ctx.project_id
            params['lang_iso'] = l
            params['replace'] = 1 if replace else 0
            params['fill_empty'] = 1 if fill_empty else 0
            params['distinguish'] = 1 if distinguish else 0
            params['hidden'] = 1 if hidden else 0

            files_lang_code = l
            if res.files_dir_map and l in res.files_dir_map:
                files_lang_code = res.files_dir_map[l]

            files_dir = res.files_dir.replace('%LANG_ISO%', files_lang_code)
            for f in files:
                file_path = os.path.join(files_dir, f)
                file_params = {'file': open(file_path, 'rb')}
                click.echo("Uploading %s..." % file_path)
                resp = requests.post(IMPORT, data=params, files=file_params)
                if resp.status_code != 200:
                    click.echo("Something went wrong when uploading {0} "
                        "(error:{1})!".format(file_path, resp.status_code))
                    return
                click.echo("Uploaded!")
                time.sleep(4)


if __name__ == '__main__':
    cli(obj={})
