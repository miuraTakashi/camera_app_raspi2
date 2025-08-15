#!/bin/bash

# SAMBA共有フォルダ設定スクリプト
# Raspberry Piカメラアプリ用のSAMBA共有を設定

echo "🔧 SAMBA共有フォルダ設定を開始します..."
echo "=========================================="

# SAMBAのインストール確認
if ! command -v smbd &> /dev/null; then
    echo "📦 SAMBAをインストール中..."
    sudo apt-get update
    sudo apt-get install -y samba samba-common-bin
else
    echo "✅ SAMBAは既にインストールされています"
fi

# 共有フォルダの作成
SHARE_PATH="/home/pi/camera_share"
echo "📁 共有フォルダを作成中: $SHARE_PATH"
sudo mkdir -p "$SHARE_PATH/photos"
sudo mkdir -p "$SHARE_PATH/videos"

# 権限を設定（誰でも読み書き可能）
echo "🔐 フォルダ権限を設定中..."
sudo chmod -R 777 "$SHARE_PATH"
sudo chown -R pi:pi "$SHARE_PATH"

# SAMBA設定ファイルのバックアップ
echo "💾 SAMBA設定ファイルをバックアップ中..."
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.backup

# 共有設定を追加
echo "📝 SAMBA共有設定を追加中..."
cat << EOF | sudo tee -a /etc/samba/smb.conf

# Camera App Shared Folder
[camera_share]
   comment = Camera App Shared Folder
   path = $SHARE_PATH
   browseable = yes
   writable = yes
   guest ok = yes
   create mask = 0777
   directory mask = 0777
   force user = pi
   force group = pi
EOF

# SAMBAサービスを再起動
echo "🔄 SAMBAサービスを再起動中..."
sudo systemctl restart smbd
sudo systemctl restart nmbd

# サービスの状態確認
echo "📊 SAMBAサービスの状態を確認中..."
sudo systemctl status smbd --no-pager -l

echo ""
echo "✅ SAMBA共有フォルダの設定が完了しました！"
echo ""
echo "📋 設定内容:"
echo "   共有名: camera_share"
echo "   共有パス: $SHARE_PATH"
echo "   写真フォルダ: $SHARE_PATH/photos"
echo "   動画フォルダ: $SHARE_PATH/videos"
echo ""
echo "🌐 ネットワークアクセス方法:"
echo "   Windows: \\\\$(hostname -I | awk '{print $1}')\\camera_share"
echo "   macOS: smb://$(hostname -I | awk '{print $1}')/camera_share"
echo "   Linux: smb://$(hostname -I | awk '{print $1}')/camera_share"
echo ""
echo "📝 注意: 必要に応じてファイアウォールでSAMBAポート(139, 445)を開放してください"
