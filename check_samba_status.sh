#!/bin/bash

# SAMBAの自動起動状態とサービス状態を確認するスクリプト

echo "🔍 SAMBAの自動起動状態とサービス状態を確認中..."
echo "=========================================="

# 1. SAMBAサービスの自動起動状態を確認
echo "📊 自動起動設定:"
if systemctl is-enabled smbd &> /dev/null; then
    echo "   ✅ smbd: 自動起動有効"
else
    echo "   ❌ smbd: 自動起動無効"
fi

if systemctl is-enabled nmbd &> /dev/null; then
    echo "   ✅ nmbd: 自動起動有効"
else
    echo "   ❌ nmbd: 自動起動無効"
fi

echo ""

# 2. 現在のサービス状態を確認
echo "📊 現在のサービス状態:"
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

# 3. ポートの使用状況を確認
echo "🌐 ネットワークポート状況:"
if netstat -tlnp 2>/dev/null | grep -E ":(139|445)" > /dev/null; then
    echo "   ✅ SAMBAポート開放:"
    netstat -tlnp 2>/dev/null | grep -E ":(139|445)" | while read line; do
        echo "      $line"
    done
else
    echo "   ❌ SAMBAポートが開放されていません"
fi

echo ""

# 4. 共有設定の確認
echo "📁 共有設定確認:"
if [ -f /etc/samba/smb.conf ]; then
    echo "   ✅ SAMBA設定ファイル存在"
    if grep -q "\[public\]" /etc/samba/smb.conf; then
        echo "   ✅ public共有設定確認"
    else
        echo "   ❌ public共有設定が見つかりません"
    fi
else
    echo "   ❌ SAMBA設定ファイルが見つかりません"
fi

echo ""

# 5. 自動起動の有効化方法
echo "🔧 自動起動の有効化方法:"
echo "   以下のコマンドで自動起動を有効にできます:"
echo "   sudo systemctl enable smbd"
echo "   sudo systemctl enable nmbd"
echo ""

# 6. サービスの手動起動方法
echo "🚀 サービスの手動起動方法:"
echo "   以下のコマンドでサービスを起動できます:"
echo "   sudo systemctl start smbd"
echo "   sudo systemctl start nmbd"
echo ""

# 7. 設定の再読み込み方法
echo "🔄 設定の再読み込み方法:"
echo "   SAMBA設定を変更した場合は以下を実行:"
echo "   sudo systemctl restart smbd"
echo "   sudo systemctl restart nmbd"
