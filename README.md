# rasp-waterflow

KEYENCE の クランプオン式流量センサ FD-Q10C と IO-LINK で通信を行なって
流量を取得するスクリプトです．

## ハード構成

LTC2874 のデータシートにある「標準的応用例」に従って回路を組み，
SPI と UART で Raspberry Pi と接続します．

## ソフト設定

Ubuntu を使っている場合，`/boot/firmware/usercfg.txt` に下記の設定を行います．

    dtparam=spi=on
    enable_uart=1
    dtoverlay=disable-bt

## 使用方法

FD-Q10C と接続した状態で，`water_flow.py` を実行すると，現在の流量が表示されます．

