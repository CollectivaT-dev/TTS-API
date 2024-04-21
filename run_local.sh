export USE_CUDA=0  #1 to enable GPU inference
export TTS_LOG_PATH=devapp.log
gunicorn server:app -b :5050 -t 300 --reload #-w 4 (Add this for multiple workers)