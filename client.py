import socket
import ssl
import os


# ============================================================
# CLIENT CONFIGURATION
# ============================================================

# The client connects to the server running on the local machine.
HOST = 'localhost'

# TCP port used by the file transfer server.
PORT = 12345

# Path to the file that will be securely transferred.
FILE_TO_SEND = 'test_files/testFile.txt'


# ============================================================
# TLS / SSL CONFIGURATION
# ============================================================

# Create a TLS context for client-side server authentication.
#
# SERVER_AUTH tells Python that this context will be used by
# a client that needs to verify the identity of the server.
context = ssl.create_default_context(
    ssl.Purpose.SERVER_AUTH
)


# This project uses TLS 1.2 for the encrypted connection.
#
# Setting both the minimum and maximum version to TLS 1.2
# ensures that the client will only negotiate TLS 1.2.
#
# TLS 1.2 provides encryption and authentication for the
# file transfer while avoiding the TLS 1.3 compatibility
# issue encountered during testing on this system.
context.minimum_version = ssl.TLSVersion.TLSv1_2
context.maximum_version = ssl.TLSVersion.TLSv1_2


# Load the client's certificate and private key.
#
# The client certificate allows the server to authenticate
# the client.
#
# The private key proves that the client owns the certificate
# during the TLS handshake.
#
# This is one of the components that enables mutual TLS (mTLS).
context.load_cert_chain(
    certfile="certs/client.crt",
    keyfile="certs/client.key"
)


# Load the trusted Certificate Authority certificate.
#
# The client uses this CA to verify that the server's
# certificate was issued by a trusted Certificate Authority.
context.load_verify_locations(
    "certs/ca.crt"
)


# ============================================================
# CONNECT TO THE SERVER
# ============================================================

try:

    print("Connecting to server...")


    # Create a normal TCP connection to the server.
    #
    # socket.create_connection() establishes the underlying
    # TCP connection before TLS is added on top of it.
    with socket.create_connection(
        (HOST, PORT)
    ) as sock:

        print("TCP connection established.")


        # ========================================================
        # ESTABLISH TLS CONNECTION
        # ========================================================

        # Wrap the existing TCP socket with TLS.
        #
        # server_hostname is set to "localhost" because the
        # server certificate contains localhost as its
        # Subject Alternative Name (SAN).
        #
        # The TLS handshake happens automatically when this
        # socket is created.
        with context.wrap_socket(
            sock,
            server_hostname=HOST
        ) as ssock:

            print("TLS handshake successful.")


            # Display information about the established
            # encrypted connection.
            #
            # These values confirm which TLS version and
            # cryptographic cipher suite are being used.
            print("TLS version:", ssock.version())
            print("Cipher:", ssock.cipher())


            # ====================================================
            # PREPARE FILE INFORMATION
            # ====================================================

            # Extract only the filename from the complete path.
            #
            # For example:
            #
            # test_files/testFile.txt
            #
            # becomes:
            #
            # testFile.txt
            #
            # This prevents the client from sending unnecessary
            # local directory information to the server.
            filename = os.path.basename(FILE_TO_SEND)


            # ====================================================
            # SEND FILENAME
            # ====================================================

            print("Sending filename...")


            # Send the filename first so that the server knows
            # what filename to use when saving the received file.
            #
            # The newline character acts as a delimiter telling
            # the server where the filename ends.
            ssock.sendall(
                filename.encode() + b'\n'
            )


            # ====================================================
            # SEND FILE CONTENT
            # ====================================================

            print("Sending file...")


            # Open the file in binary read mode.
            #
            # Binary mode allows the program to transfer both
            # text files and non-text files without modifying
            # their contents.
            with open(FILE_TO_SEND, 'rb') as f:

                while True:

                    # Read the file in 4096-byte chunks.
                    #
                    # Reading in chunks prevents large files from
                    # having to be loaded into memory all at once.
                    data = f.read(4096)


                    # When no data remains, the entire file
                    # has been read.
                    if not data:
                        break


                    # Send the current chunk through the
                    # encrypted TLS connection.
                    #
                    # sendall() ensures that all of the supplied
                    # data is sent before continuing.
                    ssock.sendall(data)


            # Confirm that the complete file has been sent.
            print(
                f"File '{filename}' sent successfully."
            )


            # ====================================================
            # FINISH THE FILE TRANSFER
            # ====================================================

            # Shut down only the sending side of the connection.
            #
            # This sends an EOF indication to the server so that
            # the server knows there is no more file data coming.
            #
            # The server can then finish writing the received
            # file to disk.
            ssock.shutdown(socket.SHUT_WR)


            print("Connection closed successfully.")


# ============================================================
# ERROR HANDLING
# ============================================================

except ssl.SSLError as e:

    # Handle TLS-related errors such as:
    #
    # - Certificate validation failure
    # - Invalid certificate
    # - TLS protocol errors
    # - Failed TLS handshake
    #
    # Keeping these errors separate makes it easier to identify
    # security/TLS problems during development.
    print("SSL ERROR:", e)


except ConnectionAbortedError as e:

    # Handle cases where the connection is unexpectedly
    # terminated by the operating system or remote endpoint.
    print("CONNECTION ABORTED:", e)


except OSError as e:

    # Handle network and operating-system errors such as:
    #
    # - Server unavailable
    # - Connection refused
    # - Invalid socket operation
    print("NETWORK ERROR:", e)


except FileNotFoundError as e:

    # Handle the situation where the file specified by
    # FILE_TO_SEND does not exist.
    print("FILE ERROR:", e)


except Exception as e:

    # Catch any unexpected error so the program can report
    # the problem instead of terminating without an explanation.
    print("UNEXPECTED ERROR:", e)