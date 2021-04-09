FROM nginx

RUN rm /etc/nginx/conf.d/default.conf

COPY ./portal /static/portal/gateway
COPY nginx.conf /etc/nginx/conf.d/