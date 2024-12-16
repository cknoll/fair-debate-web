# fair_debate_web Deployment (not yet tested for this app)

(Semi-) automated deployment is implemented for the target host [uberspace](https://uberspace.de/).

Run `python deployment/deploy.py` from the repo-root (where the `LICENSE` file is located).

## Manual steps:


- `cp config-example.toml config.toml`
- edit `config.toml`
- configure subdomain on uberspace:
    - `uberspace web domain add fair-debate.<username>.uber.space`
- run deployment script:
    - `deployment/deploy.py --help` (get overview)
    - `deployment/deploy.py -i` (first deployment run)
    - `deployment/deploy.py` (later runs (e.g. for updating))
- debugging:
    - `tail ~/logs/supervisord.log`
    - `tail ~/fair_debate_web-deployment/fair-debate/base_app_logfile.log`
    - `tail ~/fair_debate_web-deployment/fair-debate/django_logfile.log`
    - `tail ~/fair_debate_web-deployment/fair-debate/gunicorn_err.log`
    - running the django shell:
        - `cd ~`
        - `source fair_debate_web-venv/bin/activate`
        - `cd fair_debate_web-deployment/fair-debate`
        - `python manage.py shell`
