#!/bin/bash
mkdir static/css
mkdir static/js
mkdir static/fonts
wget -O static/js/jquery-latest.js https://code.jquery.com/jquery-3.2.1.js
wget -P static/js http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/bootstrap.min.js
wget -P static/js https://cdn.jsdelivr.net/npm/vue@2.5.13/dist/vue.js
wget -P static/js https://cdn.jsdelivr.net/npm/axios@0.12.0/dist/axios.min.js
wget -P static/js https://github.com/axios/axios/blob/master/dist/axios.min.map
wget -P static/js https://cdn.jsdelivr.net/npm/lodash@4.13.1/lodash.min.js
wget -O static/js/element-ui.js https://unpkg.com/element-ui/lib/index.js
wget -P static/css http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/css/bootstrap.min.css
wget -P static/css http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/css/bootstrap-theme.min.css
wget -O static/css/element-ui.css https://unpkg.com/element-ui/lib/theme-chalk/index.css
wget -P static/fonts http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.eot
wget -P static/fonts http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.svg
wget -P static/fonts http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.ttf
wget -P static/fonts http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.woff
wget -P static/fonts http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.woff2
