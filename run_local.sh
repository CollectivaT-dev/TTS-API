export USE_CUDA=0  #1 to enable GPU inference
gunicorn server:app -b :5050