import click
import yaml
import io
import os
import sys

from PyInquirer import prompt


@click.command()
@click.option('--source', '-s', help='Provide the path to the folder where the gitlab CI, .gitlab-ci.yml, file resides.')
@click.option('--destination', '-d', help='Optionally: Provide the path where you want to save the Bitbucket Pipeline, bitbucket-pipelines.yml, file. By default it will use the same source path.')
def main(source, destination):
    if source is None:
        click.echo(
            '--source or -s is required, you need to specify a file to export.')
        sys.exit(os.EX_CONFIG)

    gitlab_ci_file = source
    bitbucket_pipeline_file = destination
    if os.path.isdir(gitlab_ci_file):
        gitlab_ci_file = os.path.join(source, '.gitlab-ci.yml')
        if bitbucket_pipeline_file is None:
          bitbucket_pipeline_file = os.path.join(source, 'bitbucket-pipelines.yml')
    else:
        if bitbucket_pipeline_file is None:
          bitbucket_pipeline_file = os.path.join(os.path.dirname(source), 'bitbucket-pipelines.yml')
    
    if os.path.isdir(bitbucket_pipeline_file):
        gitlab_ci_file = os.path.join(destination, 'bitbucket-pipelines.yml')


    bitbucket_pipeline_data = {}
    bitbucket_pipeline_data['pipelines'] = {}
    with open(gitlab_ci_file, 'r') as stream:
        gitlab_ci_data = yaml.safe_load(stream)

        # In case there is no content
        if gitlab_ci_data is None:
            click.echo('.gitlab-ci.yml is empty')
            sys.exit(os.EX_DATAERR)
        
        # Remove everything but jobs, more info https://docs.gitlab.com/ee/ci/yaml/README.html#jobs
        reserved_keywords = [
            'image',
            'services',
            'stages',
          'types',
          'before_script',
          'after_script',
          'variables',
          'cache',
        ]
        caches = []

        if 'image' in gitlab_ci_data:
            bitbucket_pipeline_data['image'] = gitlab_ci_data['image']

        if 'cache' in gitlab_ci_data:
            # More here https://confluence.atlassian.com/bitbucket/caching-dependencies-895552876.html#Cachingdependencies-custom-caches
            bitbucket_predefined_caches = {
                '~/.composer/cache': 'composer',
                '~/.nuget/packages': 'dotnetcore',
                '~/.gradle/caches': 'gradle',
              '~/.ivy2/cache': 'ivy2',
              '~/.m2/repository': 'maven',
              'node_modules': 'node',
              '~/.cache/pip': 'pip',
              '~/.sbt': 'sbt',
              '~/.ivy2/cache': 'sbt'
            }
            if 'paths' in gitlab_ci_data['cache']:
                bitbucket_pipeline_data['definitions'] = {}
                bitbucket_pipeline_data['definitions']['caches'] = {}
                for path in gitlab_ci_data['cache']['paths']:
                    cache_key = ''.join([i for i in path if i.isalnum()])
                    stripped_path = path.rstrip('/')
                    if stripped_path not in bitbucket_predefined_caches.keys():
                        bitbucket_pipeline_data['definitions']['caches'][cache_key] = stripped_path
                        caches.append(cache_key)
                    else:
                        bitbucket_predefined_cache_key = bitbucket_predefined_caches[stripped_path]
                        if bitbucket_predefined_cache_key not in caches:
                            caches.append(bitbucket_predefined_cache_key)

        jobs_data = {key: gitlab_ci_data[key]
            for key in gitlab_ci_data if key not in reserved_keywords}
        for job_key in jobs_data:
            job = jobs_data[job_key]
            step = {key: job[key] for key in job if key in ['image', 'script']}
            step['name'] = job_key
            if 'before_script' in job and job['before_script']:
                step['script'] = job['before_script'] + \
                    (step['script'] if 'script' in step else [])
            if 'after_script' in job and job['after_script']:
                step['script'] = (
                    step['script'] if 'script' in step else []) + job['after_script']
            if caches:
                step['caches'] = list(caches)
            if 'only' in job:
                if 'branches' not in bitbucket_pipeline_data['pipelines']:
                    bitbucket_pipeline_data['pipelines']['branches'] = {}
                for branch in job['only']:
                    if branch not in bitbucket_pipeline_data['pipelines']['branches']:
                        bitbucket_pipeline_data['pipelines']['branches'][branch] = []
                    deployment = get_deployment_env('your deployment step %s in branch %s' % (job_key, branch))
                    if deployment != 'none':
                        step['deployment'] = deployment
                    bitbucket_pipeline_data['pipelines']['branches'][branch].append({ 'step': step })
            else:
                if 'default' not in bitbucket_pipeline_data['pipelines']:
                    bitbucket_pipeline_data['pipelines']['default'] = []
                deployment = get_deployment_env('default')
                if deployment != 'none':
                    step['deployment'] = deployment
                bitbucket_pipeline_data['pipelines']['default'].append({ 'step': step })

    # Let's write the file
    with io.open(bitbucket_pipeline_file, 'w', encoding='utf8') as out:
        yaml.dump(bitbucket_pipeline_data, out, default_flow_style=False, allow_unicode=True)

    click.echo('The bitbucket pipeline file has been created %s. The represented object is the following:' % bitbucket_pipeline_file)
    click.echo(bitbucket_pipeline_data)


def get_deployment_env(target):
    questions = [{
        'type': 'list',
        'name': 'deployment',
        'message': 'Select the type of environment for %s' % target,
              'choices': [
                  'None',
                'Test',
                'Staging',
                'Production'
              ]
    }]
    answers = prompt(questions)
    return answers['deployment'].lower()

if __name__ == '__main__':
    main()
