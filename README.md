# Canvas Module Content Import Tool
This code is based on the [Canvas LTI redirect tool](https://github.com/tl-its-umich-edu/canvas-lti-redirect-tool)

### Prerequisites

To follow the instructions below, you will at minimum need the following:
1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**.
1. **[Git](https://git-scm.com/downloads)**
### Installation and Setup
1. You need to web Proxy like Loophole or ngrok to run the application. Loophole offers custom domain
    ```sh
    loophole http 6000 --hostname <your-host>
    ```
1. Copy the `.env_sample` file as `.env`. 
    ```sh
    cp .env_sample .env

1. Examine the `.env` file. It will have the suggested default environment variable settings,
mostly just MySQL information as well as locations of other configuration files.

1. Edit `.env`, referring to the web proxy started above using loophole or ngrok, update the values for the settings…
   * `ALLOWED_HOSTS` — Add the **_hostname_** of the proxy.
   * `CSRF_TRUSTED_ORIGINS` — Add the **_base URL_** of the proxy.

1. Start the Docker build process (this will take some time).
    ```sh
    docker compose build
    ```

1. Start up the web server and database containers.
    ```sh
    docker compose up
    ```

1. generate Django secret using below command
```sh
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## LTI install
1. Need to run this command once docker container is up in order for LTI to work. This is important step otherwise the LTI tool launch won't happen
```sh
 docker compose exec -it web ./manage.py rotate_keys 
```

2. Create superuser using 
   ```
   docker compose exec -it web ./manage.py createsuperuser
   ```
   need to run a proxy like loophole or ngrok for LTI installation and login with that user. Go to https://{app-hostname}/admin/.  
3. Go to Canvas instance, choose Developer Keys in admin site
4. Add LTI Key
5. Choose Paste JSON method
6. Goto `LTIRegistration` to configure an LTI tool from admin console. This will create the `uuid` automatically. Hold on to that value and update the `OpenID Connect Initiation Url` in the LTI tool registration from Canvas with this id. 
   ` for Eg: https://module_import-local.loophole.site/init/0b54a91b-cac6-4c96-ba1e/`
7. use the `setup/lti-config.json` for registing the LTI tool. Replace all the `{app-hostname}` with your web proxy url and <uuid:lti-registration> with UUID value from LTI tool registration.  
8. Configure the LTI configuration from module import tool going to admin again. Give the following value. Note: `<canvas-lti-platform>: ['canvas.test', 'canvas.beta', 'canvas']` and <canvas-platform-url>: [`sso.test.canvaslms.com`, `sso.beta.canvaslms.com`, `sso.canvaslms.com`]. [Documentation](https://canvas.instructure.com/doc/api/file.lti_dev_key_config.html) Domain URL changes
      1. Name: any name
      2. Issuer: https://<canvas-instance>.instructure.com
      3. Client ID: (get this from Platform)
      4. Auth URL: https://<canvas-platform-url>.instructure.com/api/lti/authorize_redirect
      5. Access token URL: https://<canvas-platform-url>.instructure.com/login/oauth2/token
      6. Keyset URL: https://<canvas-platform-url>.instructure.com/api/lti/security/jwks
      7. DEPLOYMENT ID: get this as it is described the step 7 and paste 
9. Save
10. Go to the Canvas(platform) add the LTI tool at account/course level and copy the deployment id by clicking the setting button next to it.

## Make a user superuser
1. go to the `auth_user` table and set `is_superuser` and `is_staff` to `1` or `true` this will give the logged user access to admin interface
2. In order to access the admin interface for to https://<tool-hostname>/admin



