#!/bin/bash

# Decrypt control.py.enc to control.py using OpenSSL and the password
openssl enc -aes-256-cbc -d -in control.py.enc -out control.py -pass pass:DH0K3B44Z

# Check if decryption was successful
if [ $? -eq 0 ]; then
    echo "Decryption successful, running control.py..."
    # Run the decrypted Python script
    python3 control.py
else
    echo "Decryption failed. Please check the password or the encrypted file."
fi
