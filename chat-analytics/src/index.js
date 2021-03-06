import React from 'react'
import ReactDOM from 'react-dom'
import styles from './styles.js'

// Socket.IOでWebSocketサーバに接続
import socketio from 'socket.io-client'
const socket = socketio.connect('http://localhost:3001')

class ChatForm extends React.Component {
  constructor (props) {
    super(props)
    this.state = { name: '', message: '' }
  }
  nameChanged (e) {
    this.setState({name: e.target.value})
  }
  messageChanged (e) {
    this.setState({message: e.target.value})
  }

  send () {
    socket.emit('chat-msg', {
      name: this.state.name,
      message: this.state.message
    })
    this.setState({message: ''}) 
  }
  render () {
    return (
      <div style={styles.form}>
        Name:<br />
        <input value={this.state.name}
          onChange={e => this.nameChanged(e)} /><br />
        Message:<br />
        <input value={this.state.message}
          onChange={e => this.messageChanged(e)} /><br />
        <button onClick={e => this.send()}>Send</button>
      </div>
    )
  }
}

class ChatApp extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      logs: []
    }
  }
  componentDidMount () {
    socket.on('chat-msg', (obj) => {
      const logs2 = this.state.logs
      obj.key = 'key_' + (this.state.logs.length + 1)
      console.log(obj)
      logs2.unshift(obj) 
      this.setState({logs: logs2})
    })
  }
  render () {
    const messages = this.state.logs.map(e => (
      <div key={e.key} style={styles.log}>
        <span style={styles.name}>{e.name}</span>
        <span style={styles.msg}>: {e.message}</span>
        <p style={{clear: 'both'}} />
      </div>
    ))
    return (
      <div>
        <h1 style={styles.h1}>Real-time-chat-analytics</h1>
        <ChatForm />
        <div>{messages}</div>
      </div>
    )
  }
}

ReactDOM.render(
  <ChatApp />,
  document.getElementById('root'))
