// client.rs: Contains modules for network communications into the server. Utilizes interface.rs for the shell mode and IRC mode interface.
use std::io::{self, Write};
use std::net::TcpStream;

pub fn client() {
    let mut stream = TcpStream::connect("127.0.0.1:7878").unwrap();
    println!("Connected to the server!");

    let mut input = String::new();
    loop {
        io::stdin().read_line(&mut input).unwrap();
        stream.write_all(input.as_bytes()).unwrap();
        input.clear();
    }
}
