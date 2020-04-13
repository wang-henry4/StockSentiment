var http = require('http');
var express = require('express')
var chart_driver = require('./scripts/chart_driver')

var app = express()
app.set('views', __dirname + '/views');
app.engine('html', require('ejs').renderFile);
app.set('view engine', 'ejs');

app.get('/', chart_driver.init);

http.createServer(app).listen(8080);