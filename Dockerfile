FROM python:3.11-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:1

WORKDIR /app
COPY . /app

RUN touch /root/.Xauthority
RUN chmod +x start.sh

RUN apt-get update && apt-get install -y x11vnc wget xvfb xclip nano scrot

RUN export PASSWORD=$(grep '^X11VNC_PASSWORD=' .env | sed 's/X11VNC_PASSWORD=//;s/"//g') && \
    x11vnc -storepasswd $PASSWORD /etc/x11vnc.pass

RUN echo "alias x11vncstart='x11vnc -usepw -forever -display :1 -rfbauth /etc/x11vnc.pass'" >> /root/.bashrc

RUN wget -q https://telegram.org/dl/desktop/linux -O /tmp/telegram.tgz && \
    tar -xvf /tmp/telegram.tgz -C /opt/ && \
    rm /tmp/telegram.tgz \
    && ln -s /opt/Telegram/Telegram /usr/bin/telegram

RUN apt-get update && apt-get install -y \
    --no-install-recommends libdrm2 libgbm1

RUN apt-get install libgtk-3-0 -y

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y python3-pip libopencv-dev python3-opencv || true && \
    rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

CMD ["bash", "start.sh"]
