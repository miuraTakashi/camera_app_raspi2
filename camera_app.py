#!/usr/bin/env python3
"""
Raspberry Pi 2 Camera Application with SAMBA Network Share
Headless camera application that saves photos and videos to SAMBA shared folder
"""

import os
import sys
import time
import subprocess
import threading
import signal
import termios
import tty
import shutil
import getpass
from datetime import datetime, timezone, timedelta

# SAMBA共有フォルダ設定
CURRENT_USER = getpass.getuser()  # 現在のユーザー名を取得
SAMBA_SHARE_PATH = f'/home/{CURRENT_USER}/public'        # パブリックフォルダに変更
SAMBA_CONFIG_FILE = '/etc/samba/smb.conf'                # SAMBA設定ファイル
SHARE_NAME = 'camera_public'                              # 共有名をcamera_publicに変更

class CameraApp:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.script_dir)
        
        # ディレクトリ作成
        self.photos_dir = os.path.join(self.script_dir, 'photos')
        self.videos_dir = os.path.join(self.script_dir, 'videos')
        os.makedirs(self.photos_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        os.chmod(self.photos_dir, 0o755)
        os.chmod(self.videos_dir, 0o755)
        
        # カメラプロセス
        self.preview_process = None
        self.video_process = None
        self.is_recording = False
        
        # カメラツールの互換性チェック
        self.check_camera_compatibility()
        
        # SAMBA共有フォルダ設定
        self.setup_samba_share()
        
        # 設定
        self.quiet_mode = False
        self.original_terminal_settings = None
        
        # シグナルハンドラー設定
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 起動時のプロセスクリーンアップ
        self.cleanup_camera_processes()
        
    def setup_samba_share(self):
        """SAMBA共有フォルダの設定"""
        try:
            # 共有フォルダの作成
            os.makedirs(SAMBA_SHARE_PATH, exist_ok=True)
            os.makedirs(os.path.join(SAMBA_SHARE_PATH, 'photos'), exist_ok=True)
            os.makedirs(os.path.join(SAMBA_SHARE_PATH, 'videos'), exist_ok=True)
            
            # 権限を設定（誰でも読み書き可能）
            os.chmod(SAMBA_SHARE_PATH, 0o777)
            os.chmod(os.path.join(SAMBA_SHARE_PATH, 'photos'), 0o777)
            os.chmod(os.path.join(SAMBA_SHARE_PATH, 'videos'), 0o777)
            
            print(f"📁 Creating SAMBA shared folder: {SAMBA_SHARE_PATH}")
            print(f"   📸 Photos folder: {os.path.join(SAMBA_SHARE_PATH, 'photos')}")
            print(f"   🎥 Videos folder: {os.path.join(SAMBA_SHARE_PATH, 'videos')}")
            
            # Check SAMBA config file
            if os.path.exists(SAMBA_CONFIG_FILE):
                print("✅ SAMBA config file exists")
                self.check_samba_config()
            else:
                print("⚠️  SAMBA config file not found")
                print("   SAMBA installation and configuration required")
                
        except Exception as e:
            print(f"❌ SAMBA shared folder setup error: {e}")
            print("   Check folder creation permissions")
    
    def check_samba_config(self):
        """Check SAMBA configuration"""
        try:
            # Check SAMBA config file content
            with open(SAMBA_CONFIG_FILE, 'r') as f:
                config_content = f.read()
            
            # Check if share configuration exists
            if f'[{SHARE_NAME}]' in config_content:
                print("✅ SAMBA share configuration confirmed")
                print(f"   Share name: {SHARE_NAME}")
                print(f"   Path: {SAMBA_SHARE_PATH}")
            else:
                print("⚠️  SAMBA share configuration not found")
                print(f"   Expected share name: {SHARE_NAME}")
                print("   Add share configuration to SAMBA config file")
                self.create_samba_config()
                
        except Exception as e:
            print(f"⚠️  SAMBA config check error: {e}")
    
    def create_samba_config(self):
        """Add share configuration to SAMBA config file"""
        try:
            # Share configuration template
            share_config = f"""
[{SHARE_NAME}]
   comment = Camera App Public Shared Folder - Guest Access Allowed
   path = {SAMBA_SHARE_PATH}
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
"""
            
            print("📝 Creating SAMBA share configuration...")
            print(f"   Share name: {SHARE_NAME}")
            print("   Add the following configuration to /etc/samba/smb.conf:")
            print(share_config)
            
        except Exception as e:
            print(f"❌ SAMBA config creation error: {e}")
    
    def save_to_samba(self, file_path, file_type):
        """Save file to SAMBA shared folder"""
        try:
            file_name = os.path.basename(file_path)
            
            # Determine destination based on file type
            if file_type == "Photo":
                dest_dir = os.path.join(SAMBA_SHARE_PATH, 'photos')
                dest_path = os.path.join(dest_dir, file_name)
            else:  # Video
                dest_dir = os.path.join(SAMBA_SHARE_PATH, 'videos')
                dest_path = os.path.join(dest_dir, file_name)
            
            # Copy file to shared folder
            shutil.copy2(file_path, dest_path)
            
            # Set permissions (readable/writable by everyone)
            os.chmod(dest_path, 0o777)
            
            # Set file owner to guest user (nobody) for universal access
            try:
                import pwd
                import grp
                # Get nobody user and nogroup group
                nobody_uid = pwd.getpwnam('nobody').pw_uid
                nogroup_gid = grp.getgrnam('nogroup').gr_gid
                os.chown(dest_path, nobody_uid, nogroup_gid)
                print(f"   🔓 File owner: nobody:nogroup (Universal access)")
            except Exception as chown_error:
                print(f"⚠️  File owner setting error: {chown_error}")
                print("   Creating file with current user")
            
            # Get file attributes
            stat_info = os.stat(dest_path)
            print(f"✅ {file_type} saved to SAMBA shared folder: {file_name}")
            print(f"   Save location: {dest_path}")
            print(f"   File permissions: {oct(stat_info.st_mode)[-3:]}")
            print(f"   Network path: \\\\{self.get_ip_address()}\\{SHARE_NAME}\\{os.path.basename(dest_dir)}\\{file_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ {file_type} save error: {e}")
            return False
    
    def get_ip_address(self):
        """IPアドレスを取得"""
        try:
            # ネットワークインターフェースからIPアドレスを取得
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                ip_addresses = result.stdout.strip().split()
                # 最初のIPアドレスを返す（通常はローカルIP）
                return ip_addresses[0] if ip_addresses else "unknown"
            else:
                return "unknown"
        except Exception:
            return "unknown"

    def check_camera_compatibility(self):
        """カメラツールの互換性をチェック"""
        try:
            # raspistillのバージョンチェック
            result = subprocess.run(['raspistill', '--help'], capture_output=True, text=True, timeout=10)
            help_text = result.stdout + result.stderr
            
            # サポートされているオプションをチェック
            self.supports_immediate = '--immediate' in help_text
            self.supports_quality = '-q' in help_text
            self.supports_resolution = '-w' in help_text and '-h' in help_text
            
            print("📷 Camera tool compatibility check:")
            print(f"   --immediate: {'✅' if self.supports_immediate else '❌'}")
            print(f"   -q (quality): {'✅' if self.supports_quality else '❌'}")
            print(f"   -w/-h (resolution): {'✅' if self.supports_resolution else '❌'}")
            
        except Exception as e:
            print(f"⚠️  Compatibility check error: {e}")
            # Use safe defaults
            self.supports_immediate = False
            self.supports_quality = True
            self.supports_resolution = True

    def cleanup_camera_processes(self):
        """カメラプロセスのクリーンアップ"""
        try:
            # 既存のraspistill/raspividプロセスを強制終了
            subprocess.run(['pkill', '-f', 'raspistill'], capture_output=True)
            subprocess.run(['pkill', '-f', 'raspivid'], capture_output=True)
            time.sleep(1)
            
            # 残っているプロセスを確認
            result = subprocess.run(['pgrep', '-f', 'raspistill'], capture_output=True, text=True)
            if result.stdout:
                print(f"⚠️  Remaining raspistill processes: {result.stdout.strip()}")
                subprocess.run(['pkill', '-9', '-f', 'raspistill'], capture_output=True)
            
            result = subprocess.run(['pgrep', '-f', 'raspivid'], capture_output=True, text=True)
            if result.stdout:
                print(f"⚠️  Remaining raspivid processes: {result.stdout.strip()}")
                subprocess.run(['pkill', '-9', '-f', 'raspivid'], capture_output=True)
                
        except Exception as e:
            print(f"⚠️  Process cleanup error: {e}")

    def setup_terminal(self):
        """ターミナル設定"""
        self.original_terminal_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        self.monkey_patch_print()

    def monkey_patch_print(self):
        """print関数を修正してターミナル出力を適切に処理"""
        original_print = print
        
        def custom_print(*args, **kwargs):
            # 改行を適切に処理
            text = ' '.join(str(arg) for arg in args)
            if not text.endswith('\n'):
                text += '\r\n'
            else:
                text = text.replace('\n', '\r\n')
            sys.stdout.write(text)
            sys.stdout.flush()
        
        # グローバルなprint関数を置き換え
        import builtins
        builtins.print = custom_print

    def restore_terminal(self):
        """ターミナル設定を復元"""
        if self.original_terminal_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_terminal_settings)

    def get_timestamp(self):
        """JSTタイムスタンプを取得"""
        jst = timezone(timedelta(hours=9))
        return datetime.now(jst).strftime("%Y%m%d_%H%M%S")

    def check_disk_space(self):
        """ディスク容量をチェック"""
        try:
            usage = shutil.disk_usage(self.script_dir)
            free_gb = usage.free / (1024**3)
            return free_gb
        except Exception:
            return 0

    def cleanup_old_files(self):
        """古いファイルをクリーンアップ"""
        try:
            # Photo cleanup
            photo_files = [f for f in os.listdir(self.photos_dir) if f.endswith('.jpg')]
            photo_files.sort()
            
            # Remove old files if more than 100 photos
            if len(photo_files) > 100:
                for old_file in photo_files[:-100]:
                    os.remove(os.path.join(self.photos_dir, old_file))
                    print(f"🗑️  Removed old photo: {old_file}")
            
            # 動画のクリーンアップ
            video_files = [f for f in os.listdir(self.videos_dir) if f.endswith('.h264')]
            video_files.sort()
            
            # 50本を超える場合は古いものを削除
            if len(video_files) > 50:
                for old_file in video_files[:-50]:
                    os.remove(os.path.join(self.videos_dir, old_file))
                    print(f"🗑️  古い動画を削除: {old_file}")
                    
        except Exception as e:
            print(f"⚠️  ファイルクリーンアップエラー: {e}")

    def start_preview(self):
        """Start camera preview"""
        try:
            if self.preview_process:
                self.stop_preview()
            
            self.cleanup_camera_processes()
            
            # Start preview
            cmd = [
                'raspistill',
                '-t', '0',  # Unlimited
                '-f',  # Fullscreen
                '-n',  # No preview (headless mode)
                '-o', '/dev/null'
            ]
            
            self.preview_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            if not self.quiet_mode:
                print("📷 Camera preview started")
                
        except Exception as e:
            print(f"❌ Preview start error: {e}")

    def stop_preview(self):
        """Stop camera preview"""
        try:
            if self.preview_process:
                self.preview_process.terminate()
                self.preview_process.wait(timeout=5)
                self.preview_process = None
                
            # Check remaining processes
            result = subprocess.run(['pgrep', '-f', 'raspistill'], capture_output=True, text=True)
            if result.stdout:
                subprocess.run(['pkill', '-9', '-f', 'raspistill'], capture_output=True)
                
        except Exception as e:
            print(f"⚠️  Preview stop error: {e}")

    def take_photo(self):
        """Take photo"""
        try:
            if self.is_recording:
                print("⚠️  Video recording in progress. Stop recording before taking photo")
                return
            
            timestamp = self.get_timestamp()
            filename = f"{timestamp}.jpg"
            filepath = os.path.join(self.photos_dir, filename)
            
            # Check disk space
            free_gb = self.check_disk_space()
            if free_gb < 1.0:
                print("⚠️  Insufficient disk space")
                self.cleanup_old_files()
            
            # Pause preview
            self.stop_preview()
            time.sleep(0.5)
            
            # 写真撮影（互換性に基づいてパラメータを選択）
            cmd = ['raspistill', '-o', filepath]
            
            # Timer setting (extended for better preview)
            cmd.extend(['-t', '5000'])  # 5 seconds for better preview
            
            # Quality setting (only if supported)
            if hasattr(self, 'supports_quality') and self.supports_quality:
                cmd.extend(['-q', '90'])
            
            # Resolution setting (only if supported)
            if hasattr(self, 'supports_resolution') and self.supports_resolution:
                cmd.extend(['-w', '1920', '-h', '1080'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(filepath):
                file_size = os.path.getsize(filepath) / 1024  # KB
                print(f"📸 Photo taken successfully: {filename} ({file_size:.1f} KB)")
                
                # Save to SAMBA shared folder
                self.save_to_samba(filepath, "Photo")
                
            else:
                print(f"❌ Photo capture error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("❌ Photo capture timed out")
        except Exception as e:
            print(f"❌ Photo capture error: {e}")
        finally:
            # Resume preview
            time.sleep(0.5)
            self.start_preview()

    def start_video_recording(self):
        """動画録画開始"""
        try:
            if self.is_recording:
                print("⚠️  既に録画中です")
                return
            
            timestamp = self.get_timestamp()
            filename = f"{timestamp}.h264"
            filepath = os.path.join(self.videos_dir, filename)
            
            # ディスク容量チェック
            free_gb = self.check_disk_space()
            if free_gb < 2.0:
                print("⚠️  ディスク容量が不足しています")
                self.cleanup_old_files()
            
            # プレビューを一時停止
            self.stop_preview()
            time.sleep(0.5)
            
            # 動画録画開始
            cmd = [
                'raspivid',
                '-o', filepath,
                '-t', '0',  # 無制限
                '-f',  # フルスクリーン
                '-w', '1920',
                '-h', '1080',
                '-fps', '30'
            ]
            
            self.video_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.is_recording = True
            print(f"🎥 動画録画開始: {filename}")
            
            # プレビュー再開
            time.sleep(0.5)
            self.start_preview()
            
        except Exception as e:
            print(f"❌ 動画録画開始エラー: {e}")
            self.is_recording = False

    def stop_video_recording(self):
        """動画録画停止"""
        try:
            if not self.is_recording or not self.video_process:
                print("⚠️  録画中ではありません")
                return
            
            # 録画停止
            self.video_process.terminate()
            self.video_process.wait(timeout=5)
            self.video_process = None
            self.is_recording = False
            
            # 残っているプロセスを確認
            result = subprocess.run(['pgrep', '-f', 'raspivid'], capture_output=True, text=True)
            if result.stdout:
                subprocess.run(['pkill', '-9', '-f', 'raspivid'], capture_output=True)
            
            # 最新の動画ファイルを確認
            video_files = [f for f in os.listdir(self.videos_dir) if f.endswith('.h264')]
            if video_files:
                latest_video = max(video_files, key=lambda x: os.path.getctime(os.path.join(self.videos_dir, x)))
                filepath = os.path.join(self.videos_dir, latest_video)
                
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
                    print(f"🎥 動画録画完了: {latest_video} ({file_size:.1f} MB)")
                    
                    # SAMBA共有フォルダに保存
                    self.save_to_samba(filepath, "動画")
                    
        except Exception as e:
            print(f"❌ 動画録画停止エラー: {e}")

    def show_status(self):
        """ステータス表示"""
        try:
            # ディスク容量
            free_gb = self.check_disk_space()
            total_gb = shutil.disk_usage(self.script_dir).total / (1024**3)
            used_gb = total_gb - free_gb
            
            print("\n" + "="*50)
            print("📊 システムステータス")
            print("="*50)
            print(f"💾 ディスク容量: {used_gb:.1f}GB / {total_gb:.1f}GB (空き: {free_gb:.1f}GB)")
            
            # 写真・動画の数
            photo_count = len([f for f in os.listdir(self.photos_dir) if f.endswith('.jpg')])
            video_count = len([f for f in os.listdir(self.videos_dir) if f.endswith('.h264')])
            print(f"📸 保存済み写真: {photo_count}枚")
            print(f"🎥 保存済み動画: {video_count}本")
            
            # カメラ状態
            print(f"📷 プレビュー: {'有効' if self.preview_process else '無効'}")
            print(f"🎬 録画状態: {'録画中' if self.is_recording else '停止中'}")
            
            # Google Drive接続状態
            drive_status = "接続済み" if self.drive_service else "未接続"
            print(f"☁️  Google Drive: {drive_status}")
            
            print("="*50)
            
        except Exception as e:
            print(f"❌ ステータス表示エラー: {e}")

    def open_shell(self):
        """一時的にシェルを開く"""
        print("\n🐚 シェルセッションを開きます。終了するには 'exit' を入力してください")
        print("カメラアプリに戻るには Ctrl+C を押してください")
        
        try:
            # ターミナル設定を一時的に復元
            self.restore_terminal()
            
            # シェルを実行
            os.system('/bin/bash')
            
        except KeyboardInterrupt:
            pass
        finally:
            # ターミナル設定を再設定
            self.setup_terminal()

    def show_prompt(self):
        """プロンプト表示"""
        if not self.quiet_mode:
            print("\n🎮 キー入力待ち:")
            print("  SPACE: 写真撮影 | v: 動画録画 | p: プレビュー切り替え")
            print("  s: ステータス | h: シェル | q/ESC: 終了")

    def signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        print("\n\n🛑 終了シグナルを受信しました")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        """クリーンアップ処理"""
        try:
            print("\n🧹 クリーンアップ中...")
            
            # カメラプロセス停止
            self.stop_preview()
            self.stop_video_recording()
            
            # ターミナル設定復元
            self.restore_terminal()
            
            print("✅ クリーンアップ完了")
            print("\n🔧 サービス管理コマンド:")
            print("  サービス状態確認: sudo systemctl status camera-app-foreground.service")
            print("  サービス停止: sudo systemctl stop camera-app-foreground.service")
            print("  サービス開始: sudo systemctl start camera-app-foreground.service")
            print("  ログ確認: sudo journalctl -u camera-app-foreground.service -f")
            
            # シェルに戻る
            print("\n🐚 シェルに戻ります...")
            os.system('/bin/bash')
            
        except Exception as e:
            print(f"❌ クリーンアップエラー: {e}")
            sys.exit(1)

    def run(self):
        """メインループ"""
        try:
            # カメラツールの確認
            if not shutil.which('raspistill') or not shutil.which('raspivid'):
                print("❌ カメラツールが見つかりません")
                print("以下のコマンドでインストールしてください:")
                print("sudo apt-get update")
                print("sudo apt-get install libraspberrypi-bin")
                return
            
            print("🚀 Raspberry Pi カメラアプリ起動中...")
            print("📁 作業ディレクトリ:", self.script_dir)
            
            # ターミナル設定
            self.setup_terminal()
            
            # プレビュー開始
            self.start_preview()
            
            print("✅ アプリケーション準備完了!")
            
            # メインループ
            while True:
                self.show_prompt()
                
                # キー入力待ち
                key = sys.stdin.read(1)
                
                if key == ' ':  # SPACE
                    self.take_photo()
                elif key.lower() == 'v':
                    if self.is_recording:
                        self.stop_video_recording()
                    else:
                        self.start_video_recording()
                elif key.lower() == 'p':
                    if self.preview_process:
                        self.stop_preview()
                        print("📷 プレビュー停止")
                    else:
                        self.start_preview()
                elif key.lower() == 's':
                    self.show_status()
                elif key.lower() == 'h':
                    self.open_shell()
                elif key.lower() == 'q' or ord(key) == 27:  # q or ESC
                    break
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Ctrl+Cで終了しました")
        except Exception as e:
            print(f"\n❌ 予期しないエラー: {e}")
        finally:
            self.cleanup()

def main():
    """メイン関数"""
    try:
        app = CameraApp()
        app.run()
    except Exception as e:
        print(f"❌ アプリケーション起動エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 