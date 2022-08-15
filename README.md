# lisho
Minimalistic link shortener

<img width="1203" alt="image" src="https://user-images.githubusercontent.com/22280294/184730694-a8c3da2f-abce-45b3-89c0-41769fb4794c.png">

### Inspiration

This project is inspired by [w4/bin](https://github.com/w4/bin), which is a similarly minimalistic pastebin. (Which I also hosted on bin.hydev.org)

### Demo

Go to sh.hydev.org for demo.

### Self-Host

1. Create a google safebrowsing API key (this is free!)
2. Install docker
3. Write the following in `docker-compose.yml`

```docker-compose.yml
# docker-compose.yml
version: '3.3'
services:
  lisho:
    container_name: lisho
    restart: always
    ports:
      - 'YOUR PORT HERE:8000'
    image: hykilpikonna/lisho:latest
    environment:
      - GOOGLE_API_KEY="YOUR KEY HERE"
    build: .
```

4. `docker-compose up -d lisho && docker-compose logs -f lisho`

### Self-Host under NGINX

5. Write an NGINX config file and put it in `/etc/nginx/conf.d`:

```nginx.conf
# lisho.conf
server
{
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name YOUR.SUBDOMAIN.HERE;

    location ^~ /
    {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_pass http://localhost:YOUR PORT HERE/;
        proxy_redirect off;
    }
}

# Redirect HTTP to HTTPS for all servers.
server
{
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name default;
    return 301 https://$host$request_uri;
}
```

6. Sign a SSL certificate with `certbot` (free)
