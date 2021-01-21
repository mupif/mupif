default:
	# https://gist.github.com/vickramravichandran/c1190efbf9f1841234fcef624ef65956
	openssl genrsa -out rootCA.mupif.key 4096
	openssl req -x509 -new -nodes -key rootCA.mupif.key -sha256 -days 18000 -out rootCA.mupif.pem -subj "/C=CZ/ST=Czech Republic/L=Prague/O=TEST MuPIF Root Certificate"
	# https://unix.stackexchange.com/a/104305/9564
	for WHO in client server; do \
		openssl genrsa -out $$WHO.mupif.key; \
		openssl req -new -sha256 -key rootCA.mupif.key -out $$WHO.mupif.cert -subj '/C=CZ/ST=Czech Republic/L=Prague/O=None/CN=localhost'; \
		openssl x509 -req -in $$WHO.mupif.key -CA rootCA.mupif.pem -CAkey rootCA.mupif.key -CAcreateserial -days 18000 -sha256 -out $$WHO.mupif.cert -extfile <$(( printf "subjectAltName=DNS:localhost,DNS:127.0.0.1" )) ; \
	done




false:
	openssl req -new -key rootCA.mupif.key rsa:4096 -days 18000 -nodes -x509 \
			-keyout $$WHO.mupif.key -out $$WHO.mupif.cert \
			-subj '/C=CZ/ST=Czech Republic/L=Prague/O=TEST MuPIF certificates/CN=mupif.org' \
			-addext 'subjectAltName = DNS:localhost,IP:127.0.0.1' \
	; done
