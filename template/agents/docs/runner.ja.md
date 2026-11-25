# 実験ランナー

[English](runner.md) · [運用](OPERATIONS.ja.md)

```sh
python3 agents/tools/runner.py start probe-1 --timeout 90 -- python3 -c 'print("ok")'
python3 agents/tools/runner.py list
python3 agents/tools/runner.py status probe-1
python3 agents/tools/runner.py cancel probe-1
python3 agents/tools/runner.py recover probe-1
```

実行ごとに新しいジョブ ID を使います。コミット済みリビジョンの Git アーカイブから実行
します。既定の `--revision` は HEAD です。マニフェスト、実験と監督のログ、成果物を保存し、
実験内では成果物ディレクトリを `EXPERIMENT_ARTIFACTS` で参照できます。切り離された
POSIX 監督プロセスがタイムアウトとプロセスグループの取り消しを管理します。CPU と
ファイル単位の任意制限があり、環境の存続、メモリ、全体のディスク使用量はホストに
依存します。待機中に停止したことが分かっているジョブだけ
`recover --relaunch-queued` で起動します。コマンドの引数と `--env` は記録されるため
秘密値を渡さないでください。`--reuse-node-modules` は任意で、既存の依存と同じ
ロックファイルが必要です。

通知は既定で無効です。`runner.py capabilities` は実行ファイルのヘルプを調べます。
`CODEX_CLI_PATH` を使うと CLI の自動検出を上書きします。未指定時はプロジェクト設定、
PATH、Desktop ランタイムの順に調べます。Queue の引数に対応している必要があります。
配送の `accepted` は CLI が正常終了した状態です。スレッドへの実配送と新しいターンの
開始は別途確かめます。通知失敗時も結果は保存されています。自動再開では通知にある
`validate-wake` で所有者、世代、ジョブ、受領を検証します。穏やかな停止時の有効な通知は
停止の仕上げだけを許可します。停止状態からの再開には明示指示が必要です。

## 実配送の受入試験

1. 承認されたスタンドアロン CLI の Developer セッションと使い捨てのチェックアウトを
   使います。ポリシー、Git の状態、CLI ヘルプ、現在の所有者を確認します。制限時間を
   設け、後続ターンの起動について承認を得ます。
2. 対象課題、固定リビジョン、固有ジョブ ID、次の確認手順、スレッド ID を記録します。
   実際の所有者セッションで `runner.py start ID --timeout 60 --notify-thread THREAD --acceptance-probe -- sh -c 'sleep 20 && echo ADF_ACCEPTANCE_COMPLETED'`
   などの無害なジョブを起動します。試験には明示した正のタイムアウトと所有者の一致が
   必要です。ジョブをチェックポイントに保存して、最初のターンを終えます。
3. 人から追加入力せず同じスレッドでターンが始まるかを観察します。最初に通知の再開検証を
   実行し、終了コード、マーカー、順序、許可された処理範囲、重複処理の有無を確認します。
   Issue を変更する場合は承認された範囲で行います。
4. Queue が届かなければマニフェストと通知ログを確認し、環境エラーまたは権限不足を
   記録します。明示的な再開時にチェックポイントから続けます。実配送の合格までは
   `execution.auto_resume` を無効にしておきます。
