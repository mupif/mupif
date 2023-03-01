#/bin/sh
set -e -x
openssl genrsa -out rootCA.mupif.key 4096
openssl req -x509 -new -nodes -key rootCA.mupif.key -sha256 -days 18000 -out rootCA.mupif.cert -subj "/C=CZ/ST=Czech Republic/L=Prague/O=TEST MuPIF Root Certificate"
# https://unix.stackexchange.com/a/104305/9564
for WHO in client server; do
	openssl req -newkey rsa:2048 -nodes -keyout $WHO.mupif.key -subj "/C=CZ/ST=CZ/L=Prague/CN=mupif.org" -out $WHO.mupif.csr
	openssl x509 -req -extfile <(printf "subjectAltName=DNS:localhost,IP:127.0.0.1") -days 18000 -in $WHO.mupif.csr -CA rootCA.mupif.cert -CAkey rootCA.mupif.key -CAcreateserial -out $WHO.mupif.cert
done


