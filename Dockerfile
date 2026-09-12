FROM python:3.11-slim

WORKDIR /app

COPY render_redirect.py .

ENV PORT=10000

EXPOSE 10000

CMD ["python", "render_redirect.py"]
