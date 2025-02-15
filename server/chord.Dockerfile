from chord_base

workdir /app

copy server/routing.sh /app
copy server/base_chord.py /app

run chmod +x /app/routing.sh

entrypoint [ "/app/routing.sh" ]