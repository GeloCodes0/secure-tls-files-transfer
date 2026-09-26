# Secure TLS File Transfer

A Python-based secure file transfer system using **TCP, TLS 1.2, and mutual TLS (mTLS)** to provide encrypted and authenticated client-server communication.

## Overview

This project implements a secure client-server file transfer system using Python's built-in `socket` and `ssl` libraries.

The system uses **mutual TLS (mTLS)**, meaning both the server and client authenticate each other using X.509 certificates signed by a trusted Certificate Authority (CA).

The project demonstrates practical concepts in:

* Network programming
* TCP client-server communication
* TLS encryption
* Mutual TLS authentication
* X.509 certificates and Certificate Authorities
* Secure file transfer
* Basic path traversal protection
* Chunked binary file transmission

## Architecture

```text
                Mutual TLS Connection
        ┌─────────────────────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────┐       TCP/TLS       ┌──────────────┐
│    Client    │ ◄─────────────────► │    Server    │
│              │                     │              │
│ client.crt   │                     │ server.crt   │
│ client.key   │                     │ server.key   │
└──────────────┘                     └──────────────┘
        │                                 │
        └──────────────┬──────────────────┘
                       │
                 Trusted CA
                  ca.crt
```

### Communication flow

1. The client establishes a TCP connection to the server.
2. TLS negotiation begins.
3. The server presents its certificate to the client.
4. The client verifies the server certificate against the trusted CA.
5. The client presents its certificate to the server.
6. The server verifies the client certificate against the trusted CA.
7. Once mutual authentication succeeds, an encrypted TLS connection is established.
8. The client sends the filename followed by the file contents.
9. The server receives the file and stores it in the `received_files` directory.

## Security Features

### TLS Encryption

The connection is protected using **TLS 1.2**, preventing transmitted file data from being sent as plaintext across the network.

### Mutual TLS Authentication

Unlike standard TLS where normally only the server is authenticated, this project uses **mutual TLS**.

Both parties must provide a certificate signed by the trusted Certificate Authority.

```text
Client → Server
       ← server certificate
Client certificate →
       ← Certificate verification
```

This helps prevent unauthorised clients from connecting to the file server.

### Certificate Authority

A local Certificate Authority is used to sign the server and client certificates.

```text
Certificate Authority
       │
       ├── Server Certificate
       │
       └── Client Certificate
```

The certificates are verified against the CA certificate before the connection is trusted.

### Filename Sanitisation

The server uses `os.path.basename()` when processing the received filename.

This prevents a client from supplying a path such as:

```text
../../sensitive_file.txt
```

and attempting to write outside the intended receiving directory.

### Chunked File Transfer

Files are transmitted in **4096-byte chunks** rather than being loaded entirely into memory.

This allows the application to handle larger files more efficiently.

## Technologies Used

| Technology | Purpose                              |
| ---------- | ------------------------------------ |
| Python     | Application development              |
| TCP        | Reliable client-server communication |
| TLS 1.2    | Encryption and secure communication  |
| mTLS       | Mutual client/server authentication  |
| X.509      | Digital certificates                 |
| OpenSSL    | Certificate generation               |
| `socket`   | TCP networking                       |
| `ssl`      | TLS implementation                   |

No third-party Python packages are required.

## Project Structure

```text
secure-tls-files-transfer/
│
├── Certs/
│   ├── ca.crt
│   ├── client.crt
│   └── server.crt
│
├── test_files/
│   └── testFile.txt
│
├── client.py
├── server.py
├── openssl.cnf
├── .gitignore
└── README.md
```

### Private keys

The private key files are intentionally **not included in this repository**.

The following files remain local and are excluded through `.gitignore`:

```text
ca.key
client.key
server.key
```

This prevents private cryptographic material from being accidentally published to GitHub.

## Requirements

* Python 3
* OpenSSL
* Git (for version control)

The project uses only Python's standard library.

## Certificate Generation

The certificates used by the project are generated using OpenSSL.

A Certificate Authority is first created, followed by the server and client certificates.

Example CA generation:

```powershell
openssl req -x509 -newkey rsa:4096 -keyout Certs/ca.key -out Certs/ca.crt -days 3650 -nodes -subj "/CN=GeloCodes Certificate Authority"
```

The server and client certificates are then generated and signed by the CA using the configuration in:

```text
openssl.cnf
```

The private keys should remain local and must never be committed to the repository.

## Running the Project

### 1. Start the server

Open a terminal in the project directory and run:

```powershell
python server.py
```

The server listens on:

```text
localhost:12345
```

### 2. Start the client

Open a second terminal and run:

```powershell
python client.py
```

The client connects to the server using TLS and sends:

```text
test_files/testFile.txt
```

The server stores the received file in:

```text
received_files/
```

## Example Output

### Server

```text
Server listening on localhost:12345
TCP connection accepted from ('127.0.0.1', 60898)
Starting TLS handshake...
TLS handshake successful!
TLS version: TLSv1.2
Cipher: ('ECDHE-RSA-AES256-GCM-SHA384', 'TLSv1.2', 256)
Client certificate:
...
Receiving file: testFile.txt
File received successfully: received_files\testFile.txt
```

### Client

```text
Connecting to server...
TCP connection established.
TLS handshake successful.
TLS version: TLSv1.2
Cipher: ('ECDHE-RSA-AES256-GCM-SHA384', 'TLSv1.2', 256)
Sending filename...
Sending file...
File 'testFile.txt' sent successfully.
Connection closed successfully.
```

## What I Learned

This project provided practical experience with:

* TCP socket programming
* Client-server architecture
* TLS configuration
* Mutual TLS authentication
* X.509 certificates
* Certificate Authorities
* Secure key management
* Binary file transmission
* Network security controls
* Basic defensive programming

## Future Improvements

Potential improvements include:

* Supporting multiple simultaneous clients
* Adding file integrity verification using hashes
* Implementing a structured message protocol
* Adding configurable host and port settings
* Improving logging and monitoring
* Adding authentication policies for multiple trusted clients
* Investigating TLS 1.3 compatibility
* Adding automated tests

## Disclaimer

This project was developed as a networking and cybersecurity learning project and is **not intended to be used as a production file transfer system without additional security hardening, testing, and operational controls**.
