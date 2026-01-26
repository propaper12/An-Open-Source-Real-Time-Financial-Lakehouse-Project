FROM python:3.9-slim

# 👇 EKLE: İşletim sistemini güncelle ve Git'i yükle
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean

# dbt-postgres kütüphanesini yükle
RUN pip install dbt-postgres

WORKDIR /usr/app

COPY . .

CMD ["tail", "-f", "/dev/null"]