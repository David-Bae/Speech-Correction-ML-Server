FROM ipa-asr-dockerfile

WORKDIR /workspace

COPY environment.yml .
RUN conda env update -f environment.yml

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]