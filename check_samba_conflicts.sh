#!/bin/bash

# SAMBA設定の重複・競合を調査するスクリプト

echo "🔍 SAMBA設定の重複・競合を調査中..."
echo "======================================"

# 現在のユーザー名を取得
CURRENT_USER=$(whoami)
echo "👤 現在のユーザー: $CURRENT_USER"

# 共有フォルダのパス
SHARE_PATH="/home/$CURRENT_USER/public"

echo "📁 期待される共有フォルダ: $SHARE_PATH"
echo ""

# 1. 現在のSAMBA設定ファイルの内容を確認
echo "📝 現在のSAMBA設定ファイルの内容:"
echo "----------------------------------------"
if [ -f /etc/samba/smb.conf ]; then
    echo "✅ SAMBA設定ファイル存在: /etc/samba/smb.conf"
    echo ""
    
    # すべての共有設定を表示
    echo "🔍 定義されているすべての共有:"
    grep -n "\[.*\]" /etc/samba/smb.conf | grep -v "\[global\]"
    echo ""
    
    # public共有の詳細を表示
    echo "📋 public共有の詳細設定:"
    if grep -q "\[public\]" /etc/samba/smb.conf; then
        sed -n '/\[public\]/,/^\[/p' /etc/samba/smb.conf | grep -v '^$'
    else
        echo "❌ [public]共有が見つかりません"
    fi
    echo ""
    
    # パスが異なるpublic共有がないか確認
    echo "🔍 パスが異なるpublic共有の確認:"
    grep -A 5 -B 1 "path.*public" /etc/samba/smb.conf || echo "publicパスが見つかりません"
    echo ""
    
    # 共有名の重複チェック
    echo "🔍 共有名の重複チェック:"
    grep "\[.*\]" /etc/samba/smb.conf | grep -v "\[global\]" | sort | uniq -d
    echo ""
    
else
    echo "❌ SAMBA設定ファイルが見つかりません"
fi

# 2. 実際のファイルシステムの確認
echo "📊 実際のファイルシステムの確認:"
echo "----------------------------------------"
echo "期待される共有フォルダ:"
if [ -d "$SHARE_PATH" ]; then
    echo "✅ 存在: $SHARE_PATH"
    ls -la "$SHARE_PATH"
    echo ""
    
    if [ -d "$SHARE_PATH/photos" ]; then
        echo "photosフォルダの内容:"
        ls -la "$SHARE_PATH/photos"
        echo ""
    fi
    
    if [ -d "$SHARE_PATH/videos" ]; then
        echo "videosフォルダの内容:"
        ls -la "$SHARE_PATH/videos"
        echo ""
    fi
else
    echo "❌ 存在しません: $SHARE_PATH"
fi

# 3. 他のpublicフォルダの存在確認
echo "🔍 他のpublicフォルダの存在確認:"
echo "----------------------------------------"
echo "システム内のpublicフォルダを検索中..."
find /home -name "public" -type d 2>/dev/null | while read dir; do
    echo "📁 発見: $dir"
    if [ -d "$dir" ]; then
        echo "   内容:"
        ls -la "$dir" | head -5
        echo "   所有者: $(stat -c "%U:%G" "$dir")"
        echo "   権限: $(stat -c "%a" "$dir")"
        echo ""
    fi
done

# 4. SAMBAサービスの状態確認
echo "📊 SAMBAサービスの状態確認:"
echo "----------------------------------------"
echo "smbd サービス状態:"
sudo systemctl status smbd --no-pager -l | head -10
echo ""

# 5. 現在アクティブな共有の確認
echo "🌐 現在アクティブな共有の確認:"
echo "----------------------------------------"
echo "SAMBA共有一覧:"
sudo smbclient -L localhost -U% 2>/dev/null | grep -A 30 "Sharename" || echo "共有一覧の取得に失敗"
echo ""

# 6. ネットワーク共有の実際のパス確認
echo "🔍 ネットワーク共有の実際のパス確認:"
echo "----------------------------------------"
echo "現在のIPアドレス:"
hostname -I
echo ""

echo "ネットワーク共有パス:"
echo "Windows: \\\\$(hostname -I | awk '{print $1}')\\public"
echo "macOS: smb://$(hostname -I | awk '{print $1}')/public"
echo "Linux: smb://$(hostname -I | awk '{print $1}')/public"
echo ""

# 7. 問題の特定と解決方法
echo "💡 問題の特定と解決方法:"
echo "----------------------------------------"
echo "1. 設定の重複がある場合:"
echo "   sudo ./reset_samba_complete.sh"
echo ""
echo "2. パスが異なる場合:"
echo "   /etc/samba/smb.conf でパスを確認"
echo ""
echo "3. 別のpublic共有がある場合:"
echo "   古い設定を削除して再作成"
echo ""
echo "4. 共有名の競合がある場合:"
echo "   共有名を変更（例: camera_public）"
echo ""

echo "✅ 設定の重複・競合調査が完了しました！"
echo "上記の情報を確認して、問題の原因を特定してください。"
