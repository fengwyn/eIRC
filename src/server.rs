// server.rs: Contains modules for handling connections, channel management and administrative commands.
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Mutex};
use std::thread;


fn handle_client(mut stream: TcpStream, clients: Arc<Mutex<Vec<TcpStream>>>) {
    
    clients.lock().unwrap().push(stream.try_clone().unwrap());
    
    let mut buffer = [0; 512];

    loop {
        let bytes_read = stream.read(&mut buffer).unwrap();
        if bytes_read == 0 {
            return;
        }

        let message = String::from_utf8_lossy(&buffer[..bytes_read]).into_owned();
        println!("Message received: {}", message);

        let clients_guard = clients.lock().unwrap();
        for client in clients_guard.iter() {
            client.write_all(message.as_bytes()).unwrap();
        }
    }
}

pub fn server() {
    let listener = TcpListener::bind("127.0.0.1:7878").unwrap();
    let clients = Arc::new(Mutex::new(Vec::new()));

    for stream in listener.incoming() {
        let stream = stream.unwrap();
        let clients = Arc::clone(&clients);

        thread::spawn(move || {
            handle_client(stream, clients);
        });
    }
}
