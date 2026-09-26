import socket
import ssl
import os


# ============================================================
# SERVER CONFIGURATION
# ============================================================

# The server only accepts connections from the local machine.
# Using "localhost" means the server listens on the loopback
# interface rather than exposing the file transfer service
# directly to other devices on the network.
HOST = 'localhost'

# TCP port used by the file transfer server.
PORT = 12345


# ============================================================
# TLS / SSL CONFIGURATION
# ============================================================

# Create a TLS context for a server that will authenticate
# connecting clients.
#
# CLIENT_AUTH tells Python that this context will be used
# for server-side TLS connections where client authentication
# is required.
context = ssl.create_default_context(
    ssl.Purpose.CLIENT_AUTH
)


# This project uses TLS 1.2 for the encrypted connection.
#
# Setting both the minimum and maximum version to TLS 1.2
# means the server will only accept TLS 1.2 connections.
#
# This prevents an older TLS version from being negotiated
# and also avoids the TLS 1.3 compatibility issue encountered
# during testing on this system.
context.minimum_version = ssl.TLSVersion.TLSv1_2
context.maximum_version = ssl.TLSVersion.TLSv1_2


# Load the server's public certificate and private key.
#
# The certificate identifies the server to the client.
# The private key is used by the TLS protocol to prove that
# the server owns the certificate.
context.load_cert_chain(
    certfile="certs/server.crt",
    keyfile="certs/server.key"
)


# Require every client to provide a valid TLS certificate.
#
# This enables mutual TLS (mTLS):
#
#   Client verifies Server
#   Server verifies Client
#
# Without CERT_REQUIRED, the server would authenticate
# itself to the client but would not require the client
# to authenticate itself.
context.verify_mode = ssl.CERT_REQUIRED


# Load the trusted Certificate Authority certificate.
#
# The server uses this CA certificate to verify that the
# client's certificate was issued by a trusted authority.
#
# In this project, both the server and client certificates
# were signed by our own Certificate Authority.
context.load_verify_locations("certs/ca.crt")


# ============================================================
# TCP SERVER SOCKET
# ============================================================

# Create a standard TCP socket.
#
# AF_INET:
#   Uses IPv4 addressing.
#
# SOCK_STREAM:
#   Creates a TCP connection-oriented socket.
with socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
) as sock:

    # Bind the socket to the configured host and port.
    # This tells the operating system where the server
    # should accept incoming connections.
    sock.bind((HOST, PORT))

    # Put the socket into listening mode.
    #
    # The value 5 specifies the maximum number of connections
    # that can wait in the connection queue.
    sock.listen(5)

    print(f"Server listening on {HOST}:{PORT}")


    # ========================================================
    # WRAP TCP SOCKET WITH TLS
    # ========================================================

    # Convert the normal TCP socket into a TLS-enabled socket.
    #
    # server_side=True tells Python that this socket belongs
    # to the TLS server rather than a TLS client.
    #
    # do_handshake_on_connect=False allows the TLS handshake
    # to be performed manually after the TCP connection has
    # been accepted. This gives us explicit control over the
    # authentication stage.
    with context.wrap_socket(
        sock,
        server_side=True,
        do_handshake_on_connect=False
    ) as ssock:

        # Keep the server running so that it can accept
        # multiple file-transfer connections.
        while True:

            try:

                # ====================================================
                # ACCEPT TCP CONNECTION
                # ====================================================

                # Wait for a client to establish a TCP connection.
                #
                # accept() returns:
                #   conn -> socket used for communication
                #   addr -> client's IP address and port
                conn, addr = ssock.accept()

                print(f"TCP connection accepted from {addr}")


                try:

                    # =================================================
                    # TLS HANDSHAKE AND CLIENT AUTHENTICATION
                    # =================================================

                    # Perform the TLS handshake manually.
                    #
                    # During this process:
                    #
                    # 1. The client verifies the server certificate.
                    # 2. The server verifies the client certificate.
                    # 3. Cryptographic session keys are negotiated.
                    # 4. An encrypted TLS connection is established.
                    print("Starting TLS handshake...")

                    conn.do_handshake()

                    print("TLS handshake successful!")


                    # Display information about the established
                    # encrypted connection.
                    #
                    # These values are useful during development
                    # and demonstrate which TLS protocol and
                    # cipher suite are being used.
                    print("TLS version:", conn.version())
                    print("Cipher:", conn.cipher())


                    # Display the certificate presented by the client.
                    #
                    # This confirms that the server successfully
                    # authenticated the client certificate.
                    print("Client certificate:")
                    print(conn.getpeercert())


                    # =================================================
                    # FILE TRANSFER
                    # =================================================

                    # Keep the TLS connection open while receiving
                    # the filename and file contents.
                    with conn:

                        # ---------------------------------------------
                        # RECEIVE FILENAME
                        # ---------------------------------------------

                        # The client sends the filename first.
                        # A newline character marks the end of the
                        # filename so the server knows when the
                        # filename is complete.
                        filename = b''

                        while not filename.endswith(b'\n'):

                            # Receive one byte at a time while reading
                            # the filename.
                            data = conn.recv(1)

                            # If no data is received, the client has
                            # closed the connection.
                            if not data:
                                break

                            filename += data


                        # Convert the filename from bytes into a
                        # normal Python string and remove whitespace.
                        filename = filename.decode().strip()


                        # Make sure the client actually supplied
                        # a filename before attempting to create
                        # a file on the server.
                        if not filename:
                            print("No filename received.")
                            continue


                        # ---------------------------------------------
                        # SECURE FILENAME HANDLING
                        # ---------------------------------------------

                        # Only keep the filename itself and remove
                        # any directory information supplied by
                        # the client.
                        #
                        # This protects against path traversal
                        # attacks such as:
                        #
                        #     ../../important_file.txt
                        #
                        # Without this protection, a malicious client
                        # could potentially attempt to write a file
                        # outside the intended receiving directory.
                        filename = os.path.basename(filename)

                        print(f"Receiving file: {filename}")


                        # ---------------------------------------------
                        # CREATE OUTPUT DIRECTORY
                        # ---------------------------------------------

                        # Create the directory used for received files
                        # if it does not already exist.
                        #
                        # exist_ok=True prevents an error if the
                        # directory already exists.
                        os.makedirs(
                            "received_files",
                            exist_ok=True
                        )


                        # Build the complete destination path.
                        #
                        # All received files are stored inside the
                        # dedicated received_files directory.
                        output_path = os.path.join(
                            "received_files",
                            filename
                        )


                        # ---------------------------------------------
                        # RECEIVE FILE CONTENT
                        # ---------------------------------------------

                        # Open the destination file in binary write mode.
                        #
                        # "wb" is used because files can contain arbitrary
                        # binary data and should not be treated as text.
                        with open(output_path, "wb") as f:

                            while True:

                                # Receive the file in 4096-byte chunks.
                                #
                                # Using chunks prevents the entire file
                                # from having to be loaded into memory.
                                data = conn.recv(4096)


                                # An empty byte string means the client
                                # has finished sending the file and has
                                # closed its sending side of the connection.
                                if not data:
                                    break


                                # Write the received data to disk.
                                f.write(data)


                        # Confirm that the transfer completed successfully.
                        print(
                            f"File received successfully: {output_path}"
                        )


                # =====================================================
                # CONNECTION / TLS ERROR HANDLING
                # =====================================================

                except ssl.SSLError as e:

                    # Handle TLS-specific errors without terminating
                    # the entire server.
                    #
                    # This could occur if certificate validation fails,
                    # the TLS handshake fails, or the encrypted
                    # connection encounters a protocol error.
                    print("\n--- TLS ERROR ---")
                    print(f"{type(e).__name__}: {e}")
                    print("-----------------\n")


                except ConnectionAbortedError:

                    # Handle a client that unexpectedly aborts
                    # the connection.
                    #
                    # The server stays running and waits for the
                    # next client rather than crashing.
                    print(
                        "Connection aborted by client. "
                        "Waiting for another connection..."
                    )


                except OSError as e:

                    # Handle other operating-system/socket errors.
                    # Keeping this inside the connection loop means
                    # one failed connection does not stop the server.
                    print("\n--- SOCKET ERROR ---")
                    print(f"{type(e).__name__}: {e}")
                    print("--------------------\n")


                finally:

                    # Always close the client connection after the
                    # transfer or error has been handled.
                    #
                    # This releases the associated network resources.
                    try:
                        conn.close()
                    except Exception:
                        pass


            except KeyboardInterrupt:

                # Allow the server to be stopped cleanly with
                # Ctrl+C during development.
                print("\nServer shutting down...")
                break