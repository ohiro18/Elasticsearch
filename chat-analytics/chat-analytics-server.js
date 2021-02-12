const express = require('express')
const app = express()
const server = require('http').createServer(app)
const portNo = 3001
server.listen(portNo, () => {
  console.log('Runnig..', 'http://localhost:' + portNo)
})

app.use('/public', express.static('./public'))
app.get('/', (req, res) => { 
  res.redirect(302, '/public')
})

const socketio = require('socket.io')
const io = socketio.listen(server)
//const e2e = socketio.listen(server.idle)

io.on('connection', (socket) => {
  console.log('Connect user:', socket.client.id)

  socket.on('chat-msg', (msg) => {
    console.log('message', msg)
    io.emit('chat-msg', msg)
  })
})

