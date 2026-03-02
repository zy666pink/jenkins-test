FROM nginx:slim

ADD index.html /usr/share/nginx/html

CMD ["nginx","-g","daemon off;"]
