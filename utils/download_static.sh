#!/bin/bash
mkdir static/css
mkdir static/js
mkdir static/fonts
wget -O static/js/jquery-latest.js https://code.jquery.com/jquery-3.2.1.js
wget -P static/js http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/bootstrap.min.js
wget -P static/css http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/css/bootstrap.min.css
wget -P static/css http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/css/bootstrap-theme.min.css
wget -P static/fonts http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.eot
wget -P static/fonts http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.svg
wget -P static/fonts http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.ttf
wget -P static/fonts http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.woff
wget -P static/fonts http://ajax.aspnetcdn.com/ajax/bootstrap/3.3.7/fonts/glyphicons-halflings-regular.woff2
