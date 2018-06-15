#!/bin/bash
mkdir static/css
mkdir static/js
mkdir static/fonts

wget -O static/js/jquery-latest.js https://code.jquery.com/jquery-3.2.1.js
wget -O static/js/bootstrap.min.js http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/bootstrap.min.js
wget -O static/js/vue.js https://cdn.jsdelivr.net/npm/vue@2.5.13/dist/vue.js
wget -O static/js/axios.min.js https://cdn.jsdelivr.net/npm/axios@0.12.0/dist/axios.min.js
wget -O static/js/axios.min.map https://github.com/axios/axios/blob/master/dist/axios.min.map
wget -O static/js/lodash.min.js https://cdn.jsdelivr.net/npm/lodash@4.13.1/lodash.min.js
wget -O static/js/element-ui.js https://unpkg.com/element-ui/lib/index.js
wget -O static/js/jquery.slimscroll.js https://raw.githubusercontent.com/rochal/jQuery-slimScroll/v1.3.8/jquery.slimscroll.min.js

wget -O static/css/bootstrap.min.css http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/css/bootstrap.min.css
wget -O static/css/bootstrap-theme.min.css http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/css/bootstrap-theme.min.css
wget -O static/css/element-ui.css https://unpkg.com/element-ui/lib/theme-chalk/index.css
wget -O static/css/fonts/element-icons.woff https://unpkg.com/element-ui/lib/theme-chalk/fonts/element-icons.woff
wget -O static/css/fonts/element-icons.ttf https://unpkg.com/element-ui/lib/theme-chalk/fonts/element-icons.ttf

wget -O static/fonts/glyphicons-halflings-regular.eot http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.eot
wget -O static/fonts/glyphicons-halflings-regular.svg http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.svg
wget -O static/fonts/glyphicons-halflings-regular.ttf http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.ttf
wget -O static/fonts/glyphicons-halflings-regular.woff http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.woff
wget -O static/fonts/glyphicons-halflings-regular.woff2 http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.woff2
