# ADF の運用

[English](OPERATIONS.md) · [基盤の保守](maintenance.ja.md)

## プロジェクトの初期化

Copier 完了後、導入先を Codex で開いて `$initializer` を起動します。ローカルの
変更案、トラッカーの選択、承認事項を確認します。既存の指示、CI、Issue テンプレート、
エージェント設定を計画に反映します。実行基盤には Python 3.12 以上、Git、
POSIX 環境が必要です。GitHub モードでは `gh` も使います。

`agents/config.example.toml` に既定値があります。プロジェクトごとに変更するには
`agents/config.toml` にコピーし、書き込み前にポリシーを確認します。
GitHub を課題の正本とするには `tracker.backend = "github"` と
`tracker.github.repository` の `owner/name` を指定します。認証情報はホストの
認証管理に置きます。マシン固有の CLI は環境変数 `CODEX_CLI_PATH` で指定できます。

GitHub モードでは現行の Issue、ラベル、テンプレートを確認します。
`python3 agents/tools/research.py github label-plan` は不足、一致、競合を表示します。
承認後の `github setup-labels --approved` は不足ラベルを作成し、既存ラベルを保持します。
競合があれば一括処理を停止します。既存の分類や Issue を変更する場合は移行計画を
別途合意します。[トラッカーの操作と分類](tracker.ja.md)

## 起動と復旧

同じチェックアウトで `$coordinator` と `$developer` を別セッションで起動します。
Coordinator は提案の評価とトラッカーを担当します。Developer は固有 ID で所有権を
取得し、チェックポイントと Git の状態から復旧し、実装、検証、コミットを行います。
Coordinator の操作では Developer は起動・再開しません。作業を再開するセッションで
状態を確認します。

```sh
python3 agents/tools/research.py status
python3 agents/tools/runner.py capabilities
python3 agents/tools/runner.py list
```

ローカルトラッカーの状態と受付記録は `agents/research/` にあり、必要に応じて版管理
します。所有権、GitHub の実行チェックポイント、ジョブのログと成果物は Git 管理外の
`agents/runtime/` に保存されます。別マシンへの移動では個別に引き継ぎます。報告書は
テンプレート外のプロジェクト指定先へ置き、私的データをコミットから除外します。
停止、移管、復旧コマンドは [Developer の指示](roles/developer.md) を参照します。

任意の委任の前に `adf-worker` と利用するモデルが現在の Codex で使えるかを確認します。
役割の指示で同時一件に制限します。既存エージェントと互換性がある場合は、プロジェクトの
Codex 設定で `[agents] max_concurrent_threads_per_session = 1` を指定できます。
委任には承認が必要で、再委任は禁止です。[Codex サブエージェント](https://learn.chatgpt.com/docs/agent-configuration/subagents)

## 権限と受け入れ試験

```sh
python3 agents/tools/inspect_environment.py
python3 agents/tools/inspect_environment.py --github OWNER/NAME
python3 -m unittest discover -s agents/tools/tests
```

診断は状態を作らず、ローカル機能と指定時の GitHub 読み取りを調べます。OS のアクセス
判定は参考情報です。リポジトリの `allow`、`ask`、`deny` は有効なサンドボックス、
承認ポリシー、サービス側の権限と併せて適用されます。GitHub の読み取り成功と閲覧者ロール
から Issue やラベルの書き込み成功は判断できません。実際の Desktop 版、現在の
サンドボックス、承認条件、使えない機能を記録します。役割の開始時にも必要な機能を
再確認します。不足する権限はホストの承認機能と GitHub の正式なリポジトリ権限で対処します。
[Codex の権限](https://developers.openai.com/codex/agent-approvals-security)

| 機能 | 必要な操作と受入証拠 |
| --- | --- |
| ローカル Coordinator | リポジトリと研究記録の読み取り。依頼内容に応じて受付ファイルを書く権限。 |
| ローカル Developer | ソース、実行領域、研究領域への書き込み。コミットには Git メタデータへの書き込み。使い捨て Git リポジトリで検証。 |
| GitHub トラッカー | ネットワーク接続と認証されたリポジトリ・Issue の読み取り。Issue とラベルの変更はサービス権限とプロジェクトの承認が必要。書き込みは許可された試験先のみ。 |
| ランナー | Git アーカイブ、実行領域への書き込み、OS のプロセス実行。時間制限付きの無害なコマンドで切り離し完走を確認。 |
| 通知・再開 | Queue、CLI セッションと app-server への実効アクセス、後続ターンの承認。配送とターン開始を個別に確認。 |
| Worker | ネイティブ認識、承認、モデル利用権限。承認された場合に限り、限定的な読み取り課題で確認。 |

項目ごとに証拠と次の作業を保存します。結果は成功、失敗、未検証、権限不足、環境制約、
対象外で区別します。ローカルのライフサイクルと模擬 GitHub・Queue はテストで検証できます。
実際の通知については [ランナーの受入手順](runner.ja.md#実配送の受入試験) を参照します。
