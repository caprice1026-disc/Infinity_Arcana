# Phase 0のコンテンツ契約と22原型を実装する

このExecPlanは進行中の作業を記録する生きた文書である。`Progress`、`Surprises & Discoveries`、`Decision Log`、`Outcomes & Retrospective`を作業に合わせて更新する。

この文書はリポジトリ直下の`PLANS.md`に従って維持する。

## Purpose / Big Picture

この変更により、無限アルカナのアプリケーションとコンテンツ生成パイプラインが共通して利用できる、機械検証可能なJSON契約が初めて成立する。開発者は22の大アルカナ原型を読み込み、架空アルカナがどの原型を継承するかを判定できる。また、カード画像をカード本体へ直接パスとして埋め込まず、アセットIDからローカルファイル、公開URL、リモートオブジェクトストレージのいずれかへ解決できる。

リポジトリルートで`npm install`に続けて`npm run validate:content`を実行し、22原型、サンプルカード、画像アセット台帳、manifestがすべて検証済みと表示されれば動作を確認できる。

## Progress

- [x] (2026-07-19 17:16Z) 既存の要件定義、`AGENTS.md`、`PLANS.md`を確認した。
- [x] (2026-07-19 17:24Z) JSON Schemaとコンテンツ検証CLIを追加した。
- [x] (2026-07-19 17:25Z) 大アルカナ22原型の初版JSONを追加した。
- [x] (2026-07-19 17:26Z) 「バベルの図書館」と画像アセット台帳のサンプルを追加した。
- [x] (2026-07-19 17:28Z) 依存関係を導入し、全検証を実行した。
- [x] (2026-07-19 17:29Z) 検証結果と最終判断を本ExecPlanへ反映した。

## Surprises & Discoveries

- Observation: リポジトリは要件定義中心で、アプリケーションの言語や既存ビルドツールはまだ固定されていない。
  Evidence: ルートには設計文書があり、`package.json`と`pyproject.toml`は存在しなかった。

- Observation: 実行環境の既定npmキャッシュディレクトリが存在せず、最初の依存導入は失敗した。
  Evidence: `npm install`は`ENOENT: no such file or directory, mkdir '/root/.npm'`で終了した。`npm install --cache /tmp/infinity-arcana-npm-cache`で再実行すると6パッケージが導入され、以後の検証は成功した。これはリポジトリ内容の問題ではない。

- Observation: Ajvのstrict modeにより、`allOf`内の`minItems`にも明示的な`type: array`が必要だった。
  Evidence: 初回検証は`strict mode: missing type "array" for keyword "minItems"`で失敗した。各制約へ型を明示した後、Schemaのコンパイルとコンテンツ検証が成功した。

## Decision Log

- Decision: 公開コンテンツの正本は、アプリケーション実装から独立したJSONとJSON Schemaにする。
  Rationale: Sites軽量版と将来の通常版が同一の内容を読み込め、DB導入時にもデータを移植しやすいため。
  Date/Author: 2026-07-19 / Codex

- Decision: カードは画像パスではなく`visual.primaryAssetId`を保持し、実体の場所は`assets.json`で解決する。
  Rationale: ローカル配信、CDN URL、S3互換ストレージなどをカード定義の変更なしで切り替えるため。
  Date/Author: 2026-07-19 / Codex

- Decision: 大アルカナの番号はRider–Waite–Smith系の順序を採用し、「力」を8、「正義」を11とする。
  Rationale: 番号の流儀差を暗黙にせず、22原型の順序を決定的にするため。
  Date/Author: 2026-07-19 / Codex

- Decision: JSON SchemaはDraft 2020-12、検証実装はNode.jsとAjvを使用する。
  Rationale: Sites側のTypeScript実装と親和性があり、条件分岐を含むSchemaをビルド前に検証できるため。
  Date/Author: 2026-07-19 / Codex

## Outcomes & Retrospective

大アルカナ22原型をRider–Waite–Smith順で登録し、すべてに必須テーマ、禁止方向、正逆の基準、4相談文脈、架空アルカナ生成指針を与えた。原型、カード、画像台帳、manifestの4種類をJSON Schema Draft 2020-12で検証できる。

サンプルカード「バベルの図書館」は女教皇の必須テーマを継承し、`card-babel-library-front`を参照する。画像台帳は同じアセットにSites同梱用のローカルWebPと、S3互換ストレージ上の原寸PNGを登録する例になっている。画像自体は未制作なのでカードを`draft`、画像を`planned`とした。

`npm run validate:content`は22原型、1カード、1アセットの構造、件数、番号、manifest、原型継承、画像参照を検証し、終了コード0で完了した。次の段階ではdomainとpackのSchema・実データを追加し、画像制作後にアセットを`available`、カードをレビュー後に`published`へ移行する。

## Context and Orientation

`infinite-arcana-requirements-design.md`は、22の既存大アルカナを「原型」、各原型を独自世界の象徴として表現したカードを「架空アルカナ」と呼ぶ。原型の中心的意味は架空アルカナが必ず継承し、表現、物語、正逆の助言をカード側で拡張する。

今回追加する`packages/schemas/`はデータの形を定義するJSON Schema群である。`packages/content/archetypes/`には22原型、`packages/content/cards/`には架空アルカナ、`packages/content/assets/assets.json`には画像の実体を指す台帳、`packages/content/manifest.json`には公開対象ファイルの索引を置く。`tools/validate-content.mjs`は構造検証に加え、22原型の番号とID、カードから原型・画像への参照、manifestの件数を検証する。

画像の「ローカル」は、設定されたアセットルートからの相対パスを意味する。「リモートURL」は公開HTTPS URLを意味する。「オブジェクトストレージ」はS3、R2、GCS、Azure Blobなどのバケットとオブジェクトキーを意味し、認証情報はJSONへ保存せず`connectionId`から実行環境の秘密設定へ解決する。

## Plan of Work

最初に`packages/schemas/shared.schema.json`でローカライズ文字列、公開状態、公開期間などの共通型を定義する。続いて、原型、カード、画像台帳、manifestの各Schemaを追加する。カードSchemaは画像アセットIDを必須とし、画像台帳Schemaはローカル、公開URL、オブジェクトストレージを排他的な形式として受け付ける。

次に`packages/content/archetypes/`へ0から21までの22原型を作成する。各JSONには、原型の本質、旅の段階、中心的緊張、成長課題、光と影、正位置、逆位置、仕事・関係・創作・自己の基準解釈、架空アルカナ生成時に保持すべき条件を含める。

その後、`packages/content/cards/babel-library.json`を女教皇のサンプル架空アルカナとして追加する。画像は`card-babel-library-front`というIDで参照し、`packages/content/assets/assets.json`にローカル配信予定の画像として登録する。実画像はこの変更の対象外なのでアセット状態を`planned`、カード状態を`draft`とする。Schema内のexamplesでリモートURLとオブジェクトストレージの形式も示す。

最後にAjvを用いた検証CLIを実行する。JSON Schema検証だけでなく、原型が正確に22件で番号0から21が一度ずつ存在すること、参照IDが存在すること、manifest件数と列挙ファイルが一致することを確認する。

## Concrete Steps

作業ディレクトリをリポジトリルートとし、次を実行する。

    npm install
    npm run validate:content

成功時は次の要旨を含む出力になる。

    Validated 22 archetypes, 1 card, and 1 asset.
    Content validation passed.

全JSONの構文だけを独立して確認する場合は次を実行できる。

    find packages -name '*.json' -print0 | xargs -0 -n1 node -e "JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))" 

## Validation and Acceptance

`npm run validate:content`が終了コード0で完了することを必須とする。原型ファイルを1つ削除すると「expected 22 archetypes」のエラー、カードの`archetypeId`を存在しない値へ変えると参照エラー、画像IDを変えるとアセット参照エラーになることも検証CLIの責務とする。

人が確認する受け入れ条件は、`packages/content/archetypes/`に番号0から21の22ファイルが存在すること、「バベルの図書館」が`high-priestess`を参照すること、`assets.json`がローカル相対パスを保持しながらSchema上はリモート方式も許容することである。秘密鍵、アクセストークン、署名済みURLはリポジトリへ含めない。

## Idempotence and Recovery

`npm install`と`npm run validate:content`は繰り返し実行でき、コンテンツを書き換えない。検証に失敗した場合は表示されたファイルとJSONパスを修正して再実行する。公開済み原型IDは将来変更しない。誤って変更した場合は新しいIDを増やすのではなく、マージ前に元のIDへ戻す。

## Artifacts and Notes

最終検証では次の出力を得た。

    > infinity-arcana@0.1.0 validate:content
    > node tools/validate-content.mjs

    Validated 22 archetypes, 1 card, and 1 asset.
    Content validation passed.

全原型の番号を列挙し、0の愚者から21の世界まで欠番と重複がないことも確認した。

Revision note (2026-07-19): 実装と検証の完了を反映し、進捗、発見事項、成果、検証証跡を更新した。

## Interfaces and Dependencies

`packages/schemas/*.schema.json`はJSON Schema Draft 2020-12に準拠する。`tools/validate-content.mjs`はNode.jsのES Moduleとして実装し、`ajv`と`ajv-formats`だけを開発依存関係とする。

画像を解決する将来のアプリケーションは、カードの`visual.primaryAssetId`を`assets.json`の`assets[].id`へ結び付け、用途に合う`variants[]`を選ぶ。各variantの`source.type`が`local`なら`rootId`と`path`、`remote-url`なら`url`、`object-storage`なら`provider`、`connectionId`、`bucket`、`objectKey`、`access`を使用する。認証情報は`connectionId`に対応するサーバー環境設定から取得する。
