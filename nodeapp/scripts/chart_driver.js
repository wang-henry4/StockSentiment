
var data = {
    B: 123123,
    W: 180000,
    S: 666666,    
}

exports.init = function(req, res){
    res.render('index.html', data)
}