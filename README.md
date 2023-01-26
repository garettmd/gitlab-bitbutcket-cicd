# Gitlab CI to Bitbucket Pipeline

The purpose of this utility is to be able to migrate the .gitlab-ci.yml file to bitbucket-pipelines.yml

> Forked from [chrux/gitlab-bitbutcket-cicd](https://github.com/chrux/gitlab-bitbutcket-cicd) to add a couple fixes


## Docker

The easiest way to use this is to use the docker image. Run the below command from a directory with the `.gitlab-ci.yml` file that you want to migrate.

```shell
docker run -it -v ${PWD}:/files garettmd/gitlab-bitbucket-cicd:latest /files/.gitlab-ci.yml
```

This will place a shiny new `bitbucket-pipelines.yml` file in your current directory. Chances are, the results of this script alone won't get it to the final state you'd like, so you'll probably need to make some small tweaks to make it work the way you want.

If you'd rather run the code traditionally, see below.

## Dependencies

- Python 2.7.16, 3.5.2 and 3.6.8 (writter for this originally)
- PyYAML
- click
- PyInquirer

To intall them all, run:

`pip install -r requirements.txt`

## Run

`python export.py -s {source-path}`

Replace {source-path} for the directory where the .gitlab-ci.yml file is.
