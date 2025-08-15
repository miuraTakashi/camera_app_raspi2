#!/bin/bash

# SAMBA経由でファイルが見えない問題を詳細診断するスクリプト

echo "🔍 SAMBA経由でファイルが見えない問題を詳細診断中..."
echo "=================================================="

# 現在のユーザー名を取得
CURRENT_USER=$(whoami)
echo "👤 現在のユーザー: $CURRENT_USER"

# 共有フォルダのパス
SHARE_PATH="/home/$CURRENT_USER/public"

echo "📁 共有フォルダ: $SHARE_PATH"
echo ""

# 1. ファイルシステムの詳細確認
echo "📊 ファイルシステムの詳細確認:"
echo "----------------------------------------"
ls -la "$SHARE_PATH"
echo ""

if [ -d "$SHARE_PATH/photos" ]; then
    echo "📸 photosフォルダの内容:"
    ls -la "$SHARE_PATH/photos"
    echo ""
fi

if [ -d "$SHARE_PATH/videos" ]; then
    echo "🎥 videosフォルダの内容:"
    ls -la "$SHARE_PATH/videos"
    echo ""
fi

# 2. ファイル権限の詳細確認
echo "🔐 ファイル権限の詳細確認:"
echo "----------------------------------------"
if [ -d "$SHARE_PATH/photos" ]; then
    echo "photosフォルダの権限:"
    stat "$SHARE_PATH/photos"
    echo ""
    
    # 写真ファイルの権限を確認
    if [ "$(ls -A "$SHARE_PATH/photos")" ]; then
        echo "写真ファイルの権限:"
        for file in "$SHARE_PATH/photos"/*; do
            if [ -f "$file" ]; then
                echo "  $(basename "$file"): $(stat -c "%a %U:%G" "$file")"
            fi
        done
        echo ""
    fi
fi

# 3. SAMBA設定ファイルの詳細確認
echo "📝 SAMBA設定ファイルの詳細確認:"
echo "----------------------------------------"
if [ -f /etc/samba/smb.conf ]; then
    echo "✅ SAMBA設定ファイル存在"
    
    # public共有設定の詳細を表示
    echo "public共有設定の詳細:"
    sed -n '/\[public\]/,/^\[/p' /etc/samba/smb.conf | grep -v '^$'
    echo ""
    
    # グローバル設定も確認
    echo "グローバル設定:"
    grep -E "^(workgroup|security|map|hide|veto)" /etc/samba/smb.conf | head -20
    echo ""
else
    echo "❌ SAMBA設定ファイルが見つかりません"
fi

# 4. SAMBAサービスの詳細状態
echo "📊 SAMBAサービスの詳細状態:"
echo "----------------------------------------"
echo "smbd サービス状態:"
sudo systemctl status smbd --no-pager -l
echo ""

echo "nmbd サービス状態:"
sudo systemctl status nmbd --no-pager -l
echo ""

# 5. ネットワークポートの詳細確認
echo "🌐 ネットワークポートの詳細確認:"
echo "----------------------------------------"
echo "SAMBAポートの使用状況:"
sudo netstat -tlnp 2>/dev/null | grep -E ":(139|445)" || echo "ポートが見つかりません"
echo ""

echo "ファイアウォール状態:"
if command -v ufw &> /dev/null; then
    sudo ufw status
else
    echo "ufwがインストールされていません"
fi
echo ""

# 6. SAMBAログの確認
echo "📋 SAMBAログの確認:"
echo "----------------------------------------"
if [ -f /var/log/samba/log.smbd ]; then
    echo "最新のsmbdログ:"
    sudo tail -20 /var/log/samba/log.smbd
else
    echo "smbdログファイルが見つかりません"
fi
echo ""

# 7. テストファイルの作成と権限設定
echo "🧪 テストファイルの作成と権限設定:"
echo "----------------------------------------"
TEST_FILE="$SHARE_PATH/photos/test_debug_$(date +%Y%m%d_%H%M%S).txt"
echo "SAMBAデバッグ用テストファイル - $(date)" > "$TEST_FILE"
echo "このファイルがSAMBA経由で見えるかテストしてください" >> "$TEST_FILE"

# 権限を明示的に設定
sudo chmod 777 "$TEST_FILE"
sudo chown $CURRENT_USER:$CURRENT_USER "$TEST_FILE"

echo "✅ テストファイル作成: $TEST_FILE"
echo "   権限: $(stat -c "%a %U:%G" "$TEST_FILE")"
echo ""

# 8. 手動でのSAMBA共有確認
echo "🔍 手動でのSAMBA共有確認:"
echo "----------------------------------------"
echo "現在のSAMBA共有一覧:"
sudo smbclient -L localhost -U% 2>/dev/null | grep -A 20 "Sharename" || echo "共有一覧の取得に失敗"
echo ""

# 9. 推奨される修正手順
echo "💡 推奨される修正手順:"
echo "----------------------------------------"
echo "1. SAMBA設定を再作成:"
echo "   sudo ./samba_setup.sh"
echo ""
echo "2. ファイル可視性を修正:"
echo "   sudo ./fix_samba_visibility.sh"
echo ""
echo "3. SAMBAサービスを再起動:"
echo "   sudo systemctl restart smbd"
echo "   sudo systemctl restart nmbd"
echo ""
echo "4. クライアント側でキャッシュをクリア:"
echo "   Windows: ネットワークドライブを切断して再接続"
echo "   macOS: Finderで⌘+Kでサーバーに再接続"
echo "   Linux: マウントポイントをアンマウントして再マウント"
echo ""
echo "5. ファイアウォール設定を確認:"
echo "   sudo ufw allow 139"
echo "   sudo ufw allow 445"
echo ""

echo "✅ 詳細診断が完了しました！"
echo "上記の情報を確認して、問題の原因を特定してください。"
