const express = require('express');
const bodyparser =require('body-parser');
const cors = require('cors');
const mysql = require('mysql2');

const app = express();

app.use(cors());
app.use(bodyparser.json());

// app.get('/', (req, res) => {
//   res.send('Hello World!')
// })

var db = mysql.createConnection({
    host:'sh-cynosdbmysql-grp-e9bo3jzs.sql.tencentcdb.com',
    user:'admin',
    password:'ABC123!@#',
    database:'yiban',
    port:29049,
});

db.connect(err=>{
    if(err){console.log('dberr');}
    console.log('database connected...');
})


// add student userinfo data
app.post('/useradd',(req,res)=>{
    console.log(req.body.userID,'userID');
    console.log(req.body.userID,'passowrd');
    // let cid = req.body.uid;
    let userID = req.body.userID;
    let password = req.body.password
    let qr = `insert user (userID,password,type) values ('${userID}','${password}','2')`;
    db.query(qr,(err,result)=>{
        if(err){console.log(err);}
        console.log(result,'result')
        res.send({
            message:'data inserted',
        });
    })     
});



app.listen(3000,()=>{
    console.log('server running...');
});



// //database connection
// var connection = mysql.createConnection({
//     host:'sh-cynosdbmysql-grp-e9bo3jzs.sql.tencentcdb.com',
//     user:'admin',
//     password:'ABC123!@#',
//     database:'yiban',
//     port:29049,
// });
// connection.connect();//用参数与数据库进行连接
// app.get('/banner', (req, res) => {
//     res.send(str);
// })


// // //check database connection


// db.getConnection(function (err, connection) {
// 	if (err) {
// 		console.log("建立连接失败");
// 		console.log(err);
// 	} else {
// 		console.log("建立连接成功");
// 		console.log(db._allConnections.length); //  1
// 		connection.query("select * from user", function (err, rows) {
// 			if (err) {
// 				console.log("查询失败");
// 			} else {
// 				console.log(rows);
// 			}
// 			// connection.destory();
// 			console.log(db._allConnections.length); // 0
// 		});
// 	}

// });
// // db.connect(err=>{
// //     if(err){console.log('dberr');}
// //     console.log('database connected...');
// // })




// // app.listen(3000,()=>{
// //     console.log('server running...');
// // });