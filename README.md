

### Run with docker compose

```
docker compose build
docker compose up
```


### Run with installation

```
pip install -r requirements.txt
gunicorn server:app -b :5050
```

or if you have everything already setup
```
./run_local.sh
```

### Synthesis request

```
curl -L -X GET 'http://localhost:5050/api/tts?text=kaza+maraviyosa&voice=karen' --output maraviyoza.wav
```