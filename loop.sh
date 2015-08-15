until python bot.py; do
    echo "Process crashed with exit code $?. Respawning..." >&2
    sleep 5
done