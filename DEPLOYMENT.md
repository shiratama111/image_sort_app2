# 🚀 AI えびすや Bot デプロイメントガイド

このガイドでは、AI えびすや BotをクラウドサービスでホスティングするSる方法を説明します。

## 📋 前提条件

- GitHubアカウント
- Discord Bot Token
- OpenAI API Key

## 🎯 推奨デプロイメント先

### 1. Railway (推奨) 🚂

**メリット**: 
- GitHub連携で自動デプロイ
- 無料枠あり（月500時間）
- FFmpeg対応

**セットアップ**:
1. https://railway.app でアカウント作成
2. 「New Project」→「Deploy from GitHub repo」
3. 環境変数を設定:
   ```
   DISCORD_BOT_TOKEN=your_token
   OPENAI_API_KEY=your_key
   ```
4. デプロイが自動的に開始

### 2. Render 🎨

**メリット**:
- 無料プラン（月750時間）
- 自動デプロイ

**セットアップ**:
1. https://render.com でアカウント作成
2. 「New」→「Background Worker」
3. GitHubリポジトリを接続
4. 環境変数を設定

### 3. Replit 💻

**メリット**:
- ブラウザで開発可能
- 簡単なセットアップ

**セットアップ**:
1. https://replit.com でアカウント作成
2. GitHubからインポート
3. Secretsで環境変数を設定:
   - `DISCORD_BOT_TOKEN`
   - `OPENAI_API_KEY`
   - `REPLIT=true`
4. 「Run」ボタンをクリック

**常時稼働のため**:
- UptimeRobot (https://uptimerobot.com) でWebサーバーを監視

### 4. Heroku (有料) 💰

**メリット**:
- 安定性が高い
- 豊富な機能

**注意**: 無料プランは廃止されました

## ⚙️ 環境変数

すべてのプラットフォームで以下の環境変数が必要です:

```
DISCORD_BOT_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
```

## 🔧 トラブルシューティング

### FFmpegエラー
- Railway/Render: `nixpacks.toml`で自動インストール
- Replit: Shell で `nix-env -iA nixpkgs.ffmpeg` を実行

### メモリ不足
- 画像処理を無効化するか、より高いプランを検討

### Bot がオフラインになる
- UptimeRobotなどで定期的にpingを送信

## 📝 注意事項

- 無料プランには制限があります（CPU時間、メモリなど）
- 本番環境では有料プランの検討を推奨
- APIキーは必ずSecrets/環境変数で管理