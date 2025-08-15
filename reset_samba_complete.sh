#!/bin/bash

# SAMBA設定を完全にリセットして再作成するスクリプト

echo "🔄 SAMBA設定を完全にリセットして再作成中..."
echo "=============================================="

# 現在のユーザー名を取得
CURRENT_USER=$(whoami)
echo "👤 現在のユーザー: $CURRENT_USER"

# 共有フォルダのパス
SHARE_PATH="/home/$CURRENT_USER/public"

echo "📁 共有フォルダ: $SHARE_PATH"
echo ""

# 1. SAMBAサービスを停止
echo "🛑 SAMBAサービスを停止中..."
sudo systemctl stop smbd
sudo systemctl stop nmbd
echo "✅ SAMBAサービスを停止しました"
echo ""

# 2. 既存のSAMBA設定ファイルをバックアップ
echo "💾 既存のSAMBA設定ファイルをバックアップ中..."
if [ -f /etc/samba/smb.conf ]; then
    BACKUP_FILE="/etc/samba/smb.conf.backup.$(date +%Y%m%d_%H%M%S)"
    sudo cp /etc/samba/smb.conf "$BACKUP_FILE"
    echo "✅ バックアップ完了: $BACKUP_FILE"
else
    echo "⚠️  SAMBA設定ファイルが見つかりません"
fi
echo ""

# 3. 共有フォルダを完全に削除して再作成
echo "🗑️  共有フォルダを完全に削除して再作成中..."
if [ -d "$SHARE_PATH" ]; then
    sudo rm -rf "$SHARE_PATH"
    echo "✅ 既存の共有フォルダを削除しました"
fi

# 新しい共有フォルダを作成
sudo mkdir -p "$SHARE_PATH/photos"
sudo mkdir -p "$SHARE_PATH/videos"

# 権限を設定（誰でもアクセス可能）
sudo chmod -R 777 "$SHARE_PATH"
sudo chown -R nobody:nogroup "$SHARE_PATH"

echo "✅ 新しい共有フォルダを作成しました"
echo ""

# 4. SAMBA設定ファイルを完全に再作成
echo "📝 SAMBA設定ファイルを完全に再作成中..."

# 基本的なSAMBA設定ファイルを作成
sudo tee /etc/samba/smb.conf > /dev/null << EOF
[global]
   workgroup = WORKGROUP
   server string = Raspberry Pi Camera App
   security = user
   map to guest = bad user
   guest account = nobody
   dns proxy = no
   log level = 1
   log file = /var/log/samba/%m.log
   max log size = 50
   server signing = auto
   smb encrypt = auto

# Public Shared Folder (Guest Access)
[public]
   comment = Public Shared Folder - Guest Access Allowed
   path = $SHARE_PATH
   browseable = yes
   writable = yes
   guest ok = yes
   guest only = yes
   create mask = 0777
   directory mask = 0777
   force user = $CURRENT_USER
   force group = $CURRENT_USER
   hide files = /.*/lost+found/
   veto files = /.*/lost+found/
   delete veto files = yes
   map archive = no
   map hidden = no
   map system = no
   map readonly = no
   store dos attributes = no
   dos filemode = yes
EOF

echo "✅ SAMBA設定ファイルを再作成しました"
echo ""

# 5. テストファイルを作成
echo "🧪 テストファイルを作成中..."
TEST_FILE="$SHARE_PATH/photos/test_reset_$(date +%Y%m%d_%H%M%S).txt"
echo "SAMBAリセット後のテストファイル - $(date)" > "$TEST_FILE"
echo "このファイルがSAMBA経由で見えるかテストしてください" >> "$TEST_FILE"

# 権限を明示的に設定（誰でもアクセス可能）
sudo chmod 777 "$TEST_FILE"
sudo chown nobody:nogroup "$TEST_FILE"

echo "✅ テストファイル作成: $TEST_FILE"
echo "   権限: $(stat -c "%a %U:%G" "$TEST_FILE")"
echo ""

# 6. SAMBAサービスを起動
echo "🚀 SAMBAサービスを起動中..."
sudo systemctl start smbd
sudo systemctl start nmbd

# 自動起動を有効化
sudo systemctl enable smbd
sudo systemctl enable nmbd

echo "✅ SAMBAサービスを起動しました"
echo ""

# 7. サービスの状態確認
echo "📊 SAMBAサービスの状態確認中..."
if systemctl is-active smbd &> /dev/null; then
    echo "   ✅ smbd: 動作中"
else
    echo "   ❌ smbd: 停止中"
fi

if systemctl is-active nmbd &> /dev/null; then
    echo "   ✅ nmbd: 動作中"
else
    echo "   ❌ nmbd: 停止中"
fi
echo ""

# 8. ファイアウォール設定
echo "🔥 ファイアウォール設定中..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 139
    sudo ufw allow 445
    echo "✅ ファイアウォールでSAMBAポートを開放しました"
else
    echo "⚠️  ufwがインストールされていません"
fi
echo ""

# 9. 設定の確認
echo "🔍 設定の確認中..."
echo "public共有設定:"
grep -A 15 "\[public\]" /etc/samba/smb.conf
echo ""

# 10. 最終確認
echo "✅ SAMBA設定の完全リセットが完了しました！"
echo ""
echo "📋 実行した作業:"
echo "   1. SAMBAサービスを停止"
echo "   2. 既存設定をバックアップ"
echo "   3. 共有フォルダを完全に再作成"
echo "   4. SAMBA設定ファイルを完全に再作成"
echo "   5. テストファイルを作成"
echo "   6. SAMBAサービスを起動・有効化"
echo "   7. ファイアウォール設定"
echo ""
echo "🌐 ネットワークアクセス:"
echo "   Windows: \\\\$(hostname -I | awk '{print $1}')\\public"
echo "   macOS: smb://$(hostname -I | awk '{print $1}')/public"
echo "   Linux: smb://$(hostname -I | awk '{print $1}')/public"
echo ""
echo "💡 次のステップ:"
echo "   1. 上記のネットワークパスでアクセスをテスト"
echo "   2. テストファイルが表示されるか確認"
echo "   3. 問題が続く場合は debug_samba_detailed.sh を実行"
echo ""
echo "⚠️  注意: 既存の共有設定はすべて削除されました"
