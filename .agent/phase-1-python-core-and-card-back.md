# Phase 1のPython共通エンジンと知識パック共通裏面を実装する

このExecPlanは生きた文書である。作業中は `Progress`、`Surprises & Discoveries`、`Decision Log`、`Outcomes & Retrospective` を実態に合わせて更新する。リポジトリ直下の `PLANS.md` に従って維持する。

## Purpose / Big Picture

知識領域アルカナ第一集の22枚が同じカード裏面を参照できるようにする。また、UIや永続化方式から独立したPython共通エンジンを追加し、公開コンテンツを読み込んで、同じseedから同じ1枚引き・3枚引きを再現できるようにする。これによりPhase 2のSites UIや将来のFastAPI版は、同じコンテンツ契約と抽選結果を利用できる。

## Progress

- [x] (2026-07-26) 要件定義、既存ExecPlan、カード・アセットSchema、現在の入力PNGを確認した。
- [x] (2026-07-26) 裏面変換CLIと台帳・カード紐付けの失敗するPythonテストを追加して確認した。
- [x] (2026-07-26) 決定論的二段階抽選の失敗するPythonテストを追加して確認した。
- [x] (2026-07-26) Pythonの裏面変換CLIを実装し、入力PNGをWebPへ変換して22カードと台帳を更新した。
- [x] (2026-07-26) Pythonコンテンツローダー、スプレッド処理、鑑定記録型、共通テストベクトルを実装した。
- [x] (2026-07-26) Node.jsのコンテンツ検証をスプレッドとカード裏面のkind参照へ拡張した。
- [x] (2026-07-26) 領域・パック・状態・公開期間フィルター、正逆確率、候補不足位置を共通エンジンへ追加した。
- [x] (2026-07-26) 小標本の原型抽選統計テストとPython/ブラウザ固定テストベクトルを追加した。
- [x] (2026-07-26) 現在実装済み範囲のPython・Node.js検証を実行し、結果をこのExecPlanへ記録した。

## Surprises & Discoveries

- Observation: 裏面の入力PNGは1024x1535で、カード表面台帳の表示サイズ1024x1536とは1px異なる。
  Evidence: `ffprobe` が `width: 1024`、`height: 1535` を返した。
- Observation: 既存のNode.js検証とPython実装は、JSONファイルを受け渡すだけで直接依存しない。
  Evidence: `tools/validate-content.mjs` はAjvによるSchema検証専用であり、Python 3.13.1が利用可能である。

## Decision Log

- Decision: 裏面は `card-knowledge-arcana-vol-1-back` というパック共通のcard-backアセットにする。
  Rationale: 入力名と第一集の22カードが同一の裏面を持つという用途を明確にし、22個の画像複製を避けるため。
  Date/Author: 2026-07-26 / Codex
- Decision: 1024x1535のPNGは1024x1536のWebPへ変換する。
  Rationale: 既存カード表面と `2:3` presentationに揃え、画面上の表裏切り替えで寸法差が出ないようにするため。
  Date/Author: 2026-07-26 / Codex
- Decision: Phase 1の共通エンジンはPython標準ライブラリだけで実装する。
  Rationale: 要件定義がPythonの通常版APIとオフラインパイプラインを許容しており、Node.jsのAjv検証と競合しない。外部依存なしでテストと実行を再現できるため。
  Date/Author: 2026-07-26 / Codex
- Decision: 擬似乱数は `sha256-counter-v1` とし、seed文字列と呼出し回数のSHA-256から0以上1未満の値を作る。
  Rationale: Pythonと将来のTypeScriptで同じ結果を再現しやすく、テストベクトルへ固定できるため。
  Date/Author: 2026-07-26 / Codex

## Outcomes & Retrospective

裏面アセット、決定論的二段階抽選、コンテンツローダー、スプレッド、鑑定記録を実装した。Node.jsの既存Schema検証とPythonテストで、22カード・3スプレッド・共通裏面アセットの整合性を確認済みである。Sites-liteとGemini鑑定、Phase 4品質CLIの進捗は `.agent/phase-2-to-4-sites-llm-content-pipeline.md` に記録する。

## Context and Orientation

カードJSONの `visual.cardBackAssetId` はすでにSchemaで許可されているが、現在は全カードでnullである。アセット台帳は `card-back` を許可しており、`available` なローカルアセットは `tools/validate-content.mjs` が実ファイルの存在を確認する。新しい裏面は `apps/sites-lite/public/assets/cards/knowledge-arcana-vol-1/back.webp` に置き、第一集の全カードが同じアセットIDを保持する。

要件定義のPhase 1は、コンテンツローダー、Schema・参照整合性、抽選ポリシー、二段階抽選、スプレッド、鑑定記録を求める。既存のNode.js CLIは公開JSONのSchema検証を引き続き担い、`packages/core/` のPythonパッケージはコンテンツを読み、値オブジェクトとして抽選結果を返す。Python側はJSON Schemaライブラリを追加せず、Node.js検証済みのコンテンツを前提に参照と読み込みを行う。

## Plan of Work

最初にPythonのunittestで、最小台帳を使った裏面WebP変換と、22枚のカードに同じカード裏面IDを設定する操作を要求する。実装前はモジュール不在で失敗する。実装は `subprocess.run` でffmpeg/ffprobeを起動し、出力の寸法、バイト数、SHA-256を確認してから台帳へ書き戻す。

次にスプレッドSchemaと `single-card`、`situation-obstacle-advice` を公開コンテンツへ追加する。manifestをスプレッド一覧と件数を持つ版へ更新し、Node.js検証がスプレッド、カード裏面の存在とkindを検査するようにする。

続いてPythonパッケージへ、manifestから原型・カード・スプレッドを読むローダー、`sha256-counter-v1`、`balanced-two-stage-v1`、各positionのdraw、最小の鑑定記録dataclassを追加する。抽選は、フィルター済みカードを原型ごとにまとめ、原型を均等に選んでからその中のカードを選ぶ。uniqueCards/uniqueArchetypesを守れない場合は明示的に失敗する。固定seedのJSONテストベクトルを追加し、実装後のPythonテストで照合する。

## Concrete Steps

作業ディレクトリはリポジトリ直下とする。

1. `tests/test_pack_card_back.py` と `tests/test_core_draw.py` を作成し、次を実行して実装モジュール不在の失敗を確認する。

    python -m unittest discover -s tests -v

2. `tools/content_pipeline/build_pack_card_back.py` を実装し、次でテストを通す。

    python -m unittest tests.test_pack_card_back -v

3. 裏面を変換・配置する。

    python tools/content_pipeline/build_pack_card_back.py

4. Python core、スプレッドSchema/JSON、テストベクトル、Node.js検証を実装する。

5. 次の全検証を実行する。

    python -m unittest discover -s tests -v
    npm.cmd run validate:content

## Validation and Acceptance

裏面変換は、台帳にある1024x1536のローカルWebPを生成し、SHA-256とサイズを記録する。22個のカードJSONは同じcard-backアセットを参照し、Node.js検証がすべての参照とファイル存在を確認する。Pythonテストは、同一seedで同じ結果、原型二段階の選択、3枚引きのカード・原型重複排除、候補不足時のエラー、固定テストベクトルを確認する。

## Idempotence and Recovery

裏面CLIは同じ入力で再実行可能であり、内容が変わらなければ台帳versionを増やさない。入力不足、ffmpeg失敗、生成寸法の不一致では台帳を書き換えない。コンテンツローダーや抽選は読み取り専用であり、テストは一時ディレクトリを使う。

## Artifacts and Notes

実装済み範囲の検証結果は以下のとおりである。

    python -m unittest discover -s tests -v
    Ran 2 tests
    OK

    npm.cmd run validate:content
    Validated 22 archetypes, 22 cards, 1 domain, 1 pack, and 24 assets.
    Content validation passed.

    ffprobe apps/sites-lite/public/assets/cards/knowledge-arcana-vol-1/back.webp
    width: 1024
    height: 1536

裏面WebPは612382 bytes、台帳のSHA-256と一致し、`cardBackAssetId`を持つカードは22件である。manifestのasset countは24へ更新した。

## Interfaces and Dependencies

`packages/core/infinite_arcana_core/` は `load_content(content_root)`、`Sha256CounterRandom(seed)`、`BalancedTwoStagePolicy.draw(...)` を提供する。`DrawResult` はcard ID、archetype ID、orientation、position IDを持つ。`tools/content_pipeline/build_pack_card_back.py` は標準ライブラリとPATH上のffmpeg/ffprobeだけを使用する。

Revision note (2026-07-26): 裏面画像の配置依頼と、設計書のPhase 1へ進む要求に基づいて作成した。裏面変換と抽選基盤を実装し、残るPhase 1項目を明記した。
