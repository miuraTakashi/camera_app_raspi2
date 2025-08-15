#!/bin/bash

# 写真が/root/publicに行く問題を修正するスクリプト

echo "🔧 写真が/root/publicに行く問題を修正中..."
echo "=========================================="

# 現在のユーザー名を取得
CURRENT_USER=$(whoami)
echo "👤 現在のユーザー: $CURRENT_USER"

# 正しい共有フォルダのパス
CORRECT_SHARE_PATH="/home/$CURRENT_USER/public"

# 間違ったパス
WRONG_SHARE_PATH="/root/public"

echo "📁 正しい共有フォルダ: $CORRECT_SHARE_PATH"
echo "❌ 間違ったパス: $WRONG_SHARE_PATH"
echo ""

# 1. 現在のSAMBA設定を確認
echo "📝 現在のSAMBA設定を確認中..."
if [ -f /etc/samba/smb.conf ]; then
    echo "✅ SAMBA設定ファイル存在"
    
    # camera_public共有の設定を確認
    if grep -q "\[camera_public\]" /etc/samba/smb.conf; then
        echo "✅ [camera_public]共有設定が存在します"
        echo ""
        echo "現在の設定:"
        sed -n '/\[camera_public\]/,/^\[/p' /etc/samba/smb.conf | grep -v '^$'
        echo ""
        
        # パスの設定を確認
        CURRENT_PATH=$(grep -A 10 "\[camera_public\]" /etc/samba/smb.conf | grep "path" | awk '{print $3}')
        if [ -n "$CURRENT_PATH" ]; then
            echo "現在設定されているパス: $CURRENT_PATH"
            if [ "$CURRENT_PATH" = "$WRONG_SHARE_PATH" ]; then
                echo "❌ パスが間違っています！修正が必要です"
            elif [ "$CURRENT_PATH" = "$CORRECT_SHARE_PATH" ]; then
                echo "✅ パスは正しく設定されています"
            else
                echo "⚠️  予期しないパスが設定されています"
            fi
        else
            echo "❌ パスが設定されていません"
        fi
    else
        echo "❌ [camera_public]共有設定が見つかりません"
        echo "   共有設定を作成します"
    fi
else
    echo "❌ SAMBA設定ファイルが見つかりません"
    exit 1
fi
echo ""

# 2. 間違ったパスのフォルダを確認
echo "🔍 間違ったパスのフォルダを確認中..."
if [ -d "$WRONG_SHARE_PATH" ]; then
    echo "⚠️  間違ったパスのフォルダが存在します: $WRONG_SHARE_PATH"
    echo "   内容:"
    ls -la "$WRONG_SHARE_PATH"
    echo ""
    
    # 写真ファイルがあるか確認
    if [ -d "$WRONG_SHARE_PATH/photos" ]; then
        echo "photosフォルダの内容:"
        ls -la "$WRONG_SHARE_PATH/photos"
        echo ""
        
        # 写真ファイルを正しい場所に移動
        echo "📸 写真ファイルを正しい場所に移動中..."
        if [ ! -d "$CORRECT_SHARE_PATH/photos" ]; then
            sudo mkdir -p "$CORRECT_SHARE_PATH/photos"
        fi
        
        # 写真ファイルを移動
        if [ "$(ls -A "$WRONG_SHARE_PATH/photos")" ]; then
            sudo mv "$WRONG_SHARE_PATH/photos"/* "$CORRECT_SHARE_PATH/photos/"
            echo "✅ 写真ファイルを正しい場所に移動しました"
        fi
    fi
    
    # 動画ファイルがあるか確認
    if [ -d "$WRONG_SHARE_PATH/videos" ]; then
        echo "videosフォルダの内容:"
        ls -la "$WRONG_SHARE_PATH/videos"
        echo ""
        
        # 動画ファイルを正しい場所に移動
        echo "🎥 動画ファイルを正しい場所に移動中..."
        if [ ! -d "$CORRECT_SHARE_PATH/videos" ]; then
            sudo mkdir -p "$CORRECT_SHARE_PATH/videos"
        fi
        
        # 動画ファイルを移動
        if [ "$(ls -A "$WRONG_SHARE_PATH/videos")" ]; then
            sudo mv "$WRONG_SHARE_PATH/videos"/* "$CORRECT_SHARE_PATH/videos/"
            echo "✅ 動画ファイルを正しい場所に移動しました"
        fi
    fi
else
    echo "✅ 間違ったパスのフォルダは存在しません"
fi
echo ""

# 3. 正しい共有フォルダの作成・設定
echo "📁 正しい共有フォルダの作成・設定中..."
if [ ! -d "$CORRECT_SHARE_PATH" ]; then
    echo "📁 正しい共有フォルダを作成中: $CORRECT_SHARE_PATH"
    sudo mkdir -p "$CORRECT_SHARE_PATH/photos"
    sudo mkdir -p "$CORRECT_SHARE_PATH/videos"
else
    echo "✅ 正しい共有フォルダは既に存在します"
fi

# 権限を設定（誰でもアクセス可能）
sudo chmod -R 777 "$CORRECT_SHARE_PATH"
sudo chown -R nobody:nogroup "$CORRECT_SHARE_PATH"
echo "✅ フォルダ権限を設定しました"
echo ""

# 4. SAMBA設定ファイルの修正
echo "📝 SAMBA設定ファイルを修正中..."
if [ -f /etc/samba/smb.conf ]; then
    # バックアップを作成
    BACKUP_FILE="/etc/samba/smb.conf.backup.$(date +%Y%m%d_%H%M%S)"
    sudo cp /etc/samba/smb.conf "$BACKUP_FILE"
    echo "✅ バックアップ完了: $BACKUP_FILE"
    
    # 既存のcamera_public共有設定を削除
    if grep -q "\[camera_public\]" /etc/samba/smb.conf; then
        START_LINE=$(grep -n "\[camera_public\]" /etc/samba/smb.conf | cut -d: -f1)
        if [ -n "$START_LINE" ]; then
            NEXT_SHARE=$(grep -n "^\[" /etc/samba/smb.conf | grep -v "\[global\]" | awk -F: '$1 > '$START_LINE' {print $1; exit}')
            if [ -n "$NEXT_SHARE" ]; then
                END_LINE=$((NEXT_SHARE - 1))
            else
                END_LINE=$(wc -l < /etc/samba/smb.conf)
            fi
            sudo sed -i "${START_LINE},${END_LINE}d" /etc/samba/smb.conf
            echo "✅ 既存の[camera_public]共有設定を削除しました"
        fi
    fi
    
    # 正しい設定を追加
    cat << EOF | sudo tee -a /etc/samba/smb.conf

# Camera App Public Shared Folder (Guest Access)
[camera_public]
   comment = Camera App Public Shared Folder - Guest Access Allowed
   path = $CORRECT_SHARE_PATH
   browseable = yes
   writable = yes
   guest ok = yes
   guest only = yes
   create mask = 0777
   directory mask = 0777
   force user = nobody
   force group = nogroup
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

    echo "✅ 正しいSAMBA設定を追加しました"
    echo ""
    
    # 設定の確認
    echo "🔍 修正後の設定確認:"
    grep -A 20 "\[camera_public\]" /etc/samba/smb.conf
    echo ""
fi

# 5. テストファイルの作成
echo "🧪 テストファイルを作成中..."
TEST_FILE="$CORRECT_SHARE_PATH/photos/test_path_fix_$(date +%Y%m%d_%H%M%S).txt"
echo "SAMBAパス修正後のテストファイル - $(date)" > "$TEST_FILE"
echo "正しいパス: $CORRECT_SHARE_PATH" >> "$TEST_FILE"
echo "共有名: camera_public" >> "$TEST_FILE"
echo "このファイルが正しい場所に保存されるかテストしてください" >> "$TEST_FILE"

# 権限を明示的に設定（誰でもアクセス可能）
sudo chmod 777 "$TEST_FILE"
sudo chown nobody:nogroup "$TEST_FILE"

echo "✅ テストファイル作成: $TEST_FILE"
echo "   権限: $(stat -c "%a %U:%G" "$TEST_FILE")"
echo ""

# 6. SAMBAサービスを再起動
echo "🔄 SAMBAサービスを再起動中..."
sudo systemctl restart smbd
sudo systemctl restart nmbd
echo "✅ SAMBAサービスを再起動しました"
echo ""

# 7. 最終確認
echo "✅ パス問題の修正が完了しました！"
echo ""
echo "📋 実行した作業:"
echo "   1. 間違ったパスのファイルを正しい場所に移動"
echo "   2. 正しい共有フォルダを作成・設定"
echo "   3. SAMBA設定ファイルを修正"
echo "   4. テストファイルを作成"
echo "   5. SAMBAサービスを再起動"
echo ""
echo "🌐 正しいネットワークアクセス方法:"
echo "   Windows: \\\\$(hostname -I | awk '{print $1}')\\camera_public"
echo "   macOS: smb://$(hostname -I | awk '{print $1}')/camera_public"
echo "   Linux: smb://$(hostname -I | awk '{print $1}')/camera_public"
echo ""
echo "💡 次のステップ:"
echo "   1. 上記のネットワークパスでアクセスをテスト"
echo "   2. テストファイルが正しい場所に表示されるか確認"
echo "   3. カメラアプリで写真撮影をテスト"
echo ""
echo "⚠️  注意: 写真・動画は今後 $CORRECT_SHARE_PATH に保存されます"
