#!/bin/bash
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
python3 src/main.py
