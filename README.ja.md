# Autonomous Development Framework

[English](README.md)

ADF は Codex を利用するプロジェクトの研究・開発基盤です。Coordinator と
Developer が別セッションで動作し、ローカルまたは GitHub で課題を管理します。
永続チェックポイントと時間制限付きのバックグラウンド実験を利用できます。

## 導入

POSIX 環境で Git、Python 3.12 以上、Copier 9.19.1 以上を用意します。
導入先を Git リポジトリにして、ルートで以下を実行します。既存リポジトリでは
クリーンなコミットを起点にし、既存ファイルとの衝突を導入前に確認します。

```sh
copier copy --pretend /absolute/path/to/adf .
copier copy /absolute/path/to/adf .
```

利用が許可された版管理済み Git URL があれば、ローカルパスの代わりに使えます。
展開内容と回答ファイルを確認してコミットします。Codex で導入先を開き
`$initializer` を起動します。`$coordinator` と `$developer` は別セッションで起動します。
ADF の変更、更新、上流への還元には `$framework` を使います。

## ガイド

- [設計、抽出元、移行](docs/ja/architecture.md)
- [初期化、運用、権限](template/agents/docs/OPERATIONS.ja.md)
- [GitHub Issues とラベル](template/agents/docs/tracker.ja.md)
- [バックグラウンド実験と通知のトラブルシューティング](template/agents/docs/runner.ja.md)
- [導入、更新、復旧、上流への還元](template/agents/docs/maintenance.ja.md)
- [検証結果と残作業](docs/ja/verification.md)
- [リリースノート](docs/ja/releases.md)

## ローカル検証

```sh
python -m unittest discover -s template/agents/tools/tests
python -m unittest discover -s tests
```

配布試験では Copier を導入した Python を使用します。一時的なローカル Git
リポジトリを作成し、架空のデータとタグで検証します。
