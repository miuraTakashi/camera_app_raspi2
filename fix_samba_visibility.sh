#!/bin/bash

# SAMBAでファイルが見えない問題を解決するスクリプト

echo "🔧 SAMBAファイル可視性問題を解決中..."
echo "=========================================="

# 現在のユーザー名を取得
CURRENT_USER=$(whoami)
echo "👤 現在のユーザー: $CURRENT_USER"

# 共有フォルダのパス
SHARE_PATH="/home/$CURRENT_USER/public"

echo "📁 共有フォルダ: $SHARE_PATH"

# 1. フォルダとファイルの権限を確認・修正
echo ""
echo "🔐 フォルダとファイルの権限を確認・修正中..."

# 共有フォルダの権限を設定
sudo chmod -R 777 "$SHARE_PATH"
sudo chown -R $CURRENT_USER:$CURRENT_USER "$SHARE_PATH"

# サブフォルダの権限も確認
if [ -d "$SHARE_PATH/photos" ]; then
    sudo chmod 777 "$SHARE_PATH/photos"
    sudo chown $CURRENT_USER:$CURRENT_USER "$SHARE_PATH/photos"
    echo "   ✅ photosフォルダ権限設定完了"
fi

if [ -d "$SHARE_PATH/videos" ]; then
    sudo chmod 777 "$SHARE_PATH/videos"
    sudo chown $CURRENT_USER:$CURRENT_USER "$SHARE_PATH/videos"
    echo "   ✅ videosフォルダ権限設定完了"
fi

# 2. 既存ファイルの権限も修正
echo ""
echo "📄 既存ファイルの権限を修正中..."

# 写真ファイルの権限修正
if [ -d "$SHARE_PATH/photos" ]; then
    find "$SHARE_PATH/photos" -type f -exec sudo chmod 777 {} \;
    find "$SHARE_PATH/photos" -type f -exec sudo chown $CURRENT_USER:$CURRENT_USER {} \;
    echo "   ✅ 写真ファイル権限修正完了"
fi

# 動画ファイルの権限修正
if [ -d "$SHARE_PATH/videos" ]; then
    find "$SHARE_PATH/videos" -type f -exec sudo chmod 777 {} \;
    find "$SHARE_PATH/videos" -type f -exec sudo chown $CURRENT_USER:$CURRENT_USER {} \;
    echo "   ✅ 動画ファイル権限修正完了"
fi

# 3. SAMBA設定ファイルの確認・修正
echo ""
echo "📝 SAMBA設定ファイルを確認・修正中..."

if [ -f /etc/samba/smb.conf ]; then
    # バックアップを作成
    sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.backup.$(date +%Y%m%d_%H%M%S)
    
    # public共有設定を確認
    if grep -q "\[public\]" /etc/samba/smb.conf; then
        echo "   ✅ public共有設定が存在します"
        
        # 設定を更新
        sudo sed -i '/\[public\]/,/^\[/ s/^   force user = .*/   force user = '$CURRENT_USER'/' /etc/samba/smb.conf
        sudo sed -i '/\[public\]/,/^\[/ s/^   force group = .*/   force group = '$CURRENT_USER'/' /etc/samba/smb.conf
        
        echo "   ✅ ユーザー設定を更新しました"
    else
        echo "   ❌ public共有設定が見つかりません"
        echo "   samba_setup.shを実行してください"
    fi
else
    echo "   ❌ SAMBA設定ファイルが見つかりません"
    echo "   SAMBAをインストールしてください"
fi

# 4. SAMBAサービスを再起動
echo ""
echo "🔄 SAMBAサービスを再起動中..."
sudo systemctl restart smbd
sudo systemctl restart nmbd

# 5. サービスの状態確認
echo ""
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

# 6. テストファイルの作成
echo ""
echo "🧪 テストファイルを作成中..."
TEST_FILE="$SHARE_PATH/photos/test_$(date +%Y%m%d_%H%M%S).txt"
echo "SAMBA共有フォルダのテストファイル - $(date)" > "$TEST_FILE"
sudo chmod 777 "$TEST_FILE"
sudo chown $CURRENT_USER:$CURRENT_USER "$TEST_FILE"

echo "   ✅ テストファイル作成: $TEST_FILE"

echo ""
echo "✅ SAMBAファイル可視性問題の解決が完了しました！"
echo ""
echo "📋 実行した修正:"
echo "   1. フォルダ・ファイルの権限を777に設定"
echo "   2. ファイルの所有者を現在のユーザーに設定"
echo "   3. SAMBA設定ファイルのユーザー設定を更新"
echo "   4. SAMBAサービスを再起動"
echo "   5. テストファイルを作成"
echo ""
echo "🌐 ネットワークアクセス:"
echo "   Windows: \\\\$(hostname -I | awk '{print $1}')\\public"
echo "   macOS: smb://$(hostname -I | awk '{print $1}')/public"
echo "   Linux: smb://$(hostname -I | awk '{print $1}')/public"
echo ""
echo "💡 テストファイルが表示されない場合は、以下を確認してください:"
echo "   - ファイアウォール設定"
echo "   - ネットワーク接続"
echo "   - クライアント側の設定"
