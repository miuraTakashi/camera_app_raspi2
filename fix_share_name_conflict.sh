#!/bin/bash

# 共有名の競合を解決するスクリプト

echo "🔧 共有名の競合を解決中..."
echo "=============================="

# 現在のユーザー名を取得
CURRENT_USER=$(whoami)
echo "👤 現在のユーザー: $CURRENT_USER"

# 共有フォルダのパス
SHARE_PATH="/home/$CURRENT_USER/public"

# 新しい共有名（競合を避けるため）
NEW_SHARE_NAME="camera_public"

echo "📁 共有フォルダ: $SHARE_PATH"
echo "🆕 新しい共有名: $NEW_SHARE_NAME"
echo ""

# 1. 現在のSAMBA設定を確認
echo "📝 現在のSAMBA設定を確認中..."
if [ -f /etc/samba/smb.conf ]; then
    echo "✅ SAMBA設定ファイル存在"
    
    # 既存のpublic共有があるか確認
    if grep -q "\[public\]" /etc/samba/smb.conf; then
        echo "⚠️  既存の[public]共有が発見されました"
        echo "   共有名を変更して競合を避けます"
    else
        echo "✅ [public]共有は存在しません"
    fi
else
    echo "❌ SAMBA設定ファイルが見つかりません"
    exit 1
fi
echo ""

# 2. 共有フォルダの確認・作成
echo "📁 共有フォルダの確認・作成中..."
if [ ! -d "$SHARE_PATH" ]; then
    echo "📁 共有フォルダを作成中: $SHARE_PATH"
    sudo mkdir -p "$SHARE_PATH/photos"
    sudo mkdir -p "$SHARE_PATH/videos"
else
    echo "✅ 共有フォルダは既に存在します"
fi

# 権限を設定（誰でもアクセス可能）
sudo chmod -R 777 "$SHARE_PATH"
sudo chown -R nobody:nogroup "$SHARE_PATH"
echo "✅ フォルダ権限を設定しました"
echo ""

# 3. SAMBA設定ファイルのバックアップ
echo "💾 SAMBA設定ファイルをバックアップ中..."
BACKUP_FILE="/etc/samba/smb.conf.backup.$(date +%Y%m%d_%H%M%S)"
sudo cp /etc/samba/smb.conf "$BACKUP_FILE"
echo "✅ バックアップ完了: $BACKUP_FILE"
echo ""

# 4. 既存のpublic共有設定を削除
echo "🗑️  既存のpublic共有設定を削除中..."
if grep -q "\[public\]" /etc/samba/smb.conf; then
    # public共有の開始行と次の共有の開始行を特定
    START_LINE=$(grep -n "\[public\]" /etc/samba/smb.conf | cut -d: -f1)
    
    if [ -n "$START_LINE" ]; then
        # 次の共有の開始行を探す
        NEXT_SHARE=$(grep -n "^\[" /etc/samba/smb.conf | grep -v "\[global\]" | awk -F: '$1 > '$START_LINE' {print $1; exit}')
        
        if [ -n "$NEXT_SHARE" ]; then
            # public共有の終了行を次の共有の前の行に設定
            END_LINE=$((NEXT_SHARE - 1))
        else
            # 次の共有がない場合はファイルの最後まで
            END_LINE=$(wc -l < /etc/samba/smb.conf)
        fi
        
        # public共有設定を削除
        sudo sed -i "${START_LINE},${END_LINE}d" /etc/samba/smb.conf
        echo "✅ 既存の[public]共有設定を削除しました"
    fi
else
    echo "✅ [public]共有設定は存在しません"
fi
echo ""

# 5. 新しい共有設定を追加
echo "📝 新しい共有設定を追加中..."
cat << EOF | sudo tee -a /etc/samba/smb.conf

# Camera App Public Shared Folder (Guest Access)
[$NEW_SHARE_NAME]
   comment = Camera App Public Shared Folder - Guest Access Allowed
   path = $SHARE_PATH
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

echo "✅ 新しい共有設定[$NEW_SHARE_NAME]を追加しました"
echo ""

# 6. 設定の確認
echo "🔍 設定の確認中..."
echo "新しい共有設定[$NEW_SHARE_NAME]:"
grep -A 20 "\[$NEW_SHARE_NAME\]" /etc/samba/smb.conf
echo ""

# 7. テストファイルを作成
echo "🧪 テストファイルを作成中..."
TEST_FILE="$SHARE_PATH/photos/test_share_$(date +%Y%m%d_%H%M%S).txt"
echo "SAMBA共有名変更後のテストファイル - $(date)" > "$TEST_FILE"
echo "共有名: $NEW_SHARE_NAME" >> "$TEST_FILE"
echo "このファイルがSAMBA経由で見えるかテストしてください" >> "$TEST_FILE"

# 権限を明示的に設定（誰でもアクセス可能）
sudo chmod 777 "$TEST_FILE"
sudo chown nobody:nogroup "$TEST_FILE"

echo "✅ テストファイル作成: $TEST_FILE"
echo "   権限: $(stat -c "%a %U:%G" "$TEST_FILE")"
echo ""

# 8. SAMBAサービスを再起動
echo "🔄 SAMBAサービスを再起動中..."
sudo systemctl restart smbd
sudo systemctl restart nmbd
echo "✅ SAMBAサービスを再起動しました"
echo ""

# 9. サービスの状態確認
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

# 10. 最終確認
echo "✅ 共有名の競合解決が完了しました！"
echo ""
echo "📋 実行した作業:"
echo "   1. 既存の[public]共有設定を削除"
echo "   2. 新しい共有名[$NEW_SHARE_NAME]で設定を追加"
echo "   3. 共有フォルダの権限を設定"
echo "   4. テストファイルを作成"
echo "   5. SAMBAサービスを再起動"
echo ""
echo "🌐 新しいネットワークアクセス方法:"
echo "   Windows: \\\\$(hostname -I | awk '{print $1}')\\$NEW_SHARE_NAME"
echo "   macOS: smb://$(hostname -I | awk '{print $1}')/$NEW_SHARE_NAME"
echo "   Linux: smb://$(hostname -I | awk '{print $1}')/$NEW_SHARE_NAME"
echo ""
echo "💡 次のステップ:"
echo "   1. 上記の新しいネットワークパスでアクセスをテスト"
echo "   2. テストファイルが表示されるか確認"
echo "   3. 問題が続く場合は check_samba_conflicts.sh を実行"
echo ""
echo "⚠️  注意: 共有名が[public]から[$NEW_SHARE_NAME]に変更されました"
