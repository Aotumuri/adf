# ADF の保守

[English](maintenance.md) · [運用](OPERATIONS.ja.md)

## 導入と調査

ADF 上流リポジトリで `$framework` を使う場合は `template/` から Codex を起動します。

信頼できる版管理済みの ADF URL またはローカル Git の絶対パスを使います。既存プロジェクト
ではクリーンなコミットから一時ブランチかクローンを作成します。プレビューで衝突する
ファイルを調べ、各ファイルの統合方針を決めます。導入済みなら記録済みの回答と更新手順を
使います。

```sh
copier copy --pretend ADF_SOURCE .
copier copy ADF_SOURCE .
```

導入結果をレビューして回答ファイルをコミットします。Copier は導入元とタグを
`.copier-answers.yml` に記録します。このファイルの更新は Copier に任せます。
`copier check-update` と信頼できる上流のリリースノートを参照します。Skills は
`.agents/skills/` にあります。`$initializer` で既存の方針に統合し、利用機能を検証します。

## 更新と復旧

Developer と調整し、ジョブと編集が停止した区切りを確認します。導入先のコミット済み状態
から使い捨てクローンを作成し、元のコミットを記録します。既存の独自変更をコミットして
おくと Copier が統合できます。未コミットの作業は安全に統合できるまで元の作業ツリーに
保持します。

```sh
git clone --no-hardlinks "$PWD" "$candidate"
cd "$candidate"
copier update --pretend --defaults --vcs-ref "$tag"
copier update --defaults --vcs-ref "$tag" --conflict inline
git status --short
git diff
git diff --cached
git ls-files --unmerged
```

導入時の基準、上流の差分、ローカルの意図を照合して各競合を解決します。拒否ファイルの
モードでは各 `.rej` を確認します。`git diff --check`、`git diff --cached --check` と
基盤・プロジェクトの受け入れ試験を実施し、新規ファイルも確認します。回答ファイルのタグが
意図したものか確かめます。レビューした更新だけをコミットし、安全な区切りに元の
チェックアウトでクローンのローカルパスから fetch して対象コミットを cherry-pick します。
元の環境でプロジェクト設定、状態、成果物を確認します。

失敗した更新は候補クローンに残し、再試行は元のコミットから始めます。誤って元の
作業ツリーで更新したときは、失敗時点の Git 状態と差分を記録し、クリーンだった開始時点と
照合して、更新に由来するパスだけを復元します。更新で作成されたと確認できる追加分だけを
退避します。無関係な編集と Git 管理外の状態は保持します。コミット済みの更新は、
クリーンなブランチで revert の影響を確認し、後続の編集との競合を解決します。
更新操作は開始時の手順で完了させ、新しい Skill は次回の起動から使用します。

[Copier の更新、競合、復旧](https://copier.readthedocs.io/en/stable/updating/)

## 上流への還元

導入先のルートで、Copier を導入した Python を使います。補助スクリプトは記録済みの
配布元、タグ、回答から一時領域に基準を再展開し、選択した通常ファイルを作業ツリーと
比較します。独自変更を共通改善、プロジェクト固有、実験、一時的な回避策として評価します。
私的データ、固有値、認証情報、研究成果はパッチから除外します。差分は標準出力に出るので
ローカルでレビューできます。

```sh
python agents/tools/contribution.py agents/tools/runner.py > /path/to/adf.patch
git -C "$upstream_checkout" apply --check /path/to/adf.patch
git -C "$upstream_checkout" apply --3way /path/to/adf.patch
```

共通ファイルを新規追加する場合は `--new PATH` を指定します。複数指定できます。
テンプレートにあった削除ファイルは削除の差分になります。スクリプトはそのまま展開される
ファイルを `template/` に割り当てます。Jinja で内容や名前が変わる場合は意味を確認して
テンプレートを修正します。最新の上流で差分を確認し、必要に応じて競合を解決するか、
記録したタグに適用して上流ブランチへ rebase します。テンプレートと新規展開の両方を
検証します。公開権限がない場合も、レビュー済みパッチ、変更理由、テスト結果をローカルに
保存できます。承認後は上流またはフォークの作業ブランチにコミット・push し、承認された
上流に `gh pr create` で提出します。ローカルの利用と更新は提出の有無にかかわらず継続
できます。

Git タグ、ローカルマージ、回答は Copier が担当します。ADF は選択差分の逆変換と隔離した
更新手順を提供します。リリースは `vMAJOR.MINOR.PATCH` のタグと日英のリリースノートで管理します。
