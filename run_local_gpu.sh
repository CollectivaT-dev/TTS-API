export USE_CUDA=1
gunicorn server:app -b :5050