# 知識領域アルカナ第一集を22原型で実装する

このExecPlanは進行中の作業を記録する生きた文書である。Progress、Surprises & Discoveries、Decision Log、Outcomes & Retrospectiveを作業に合わせて更新する。

この文書はリポジトリ直下のPLANS.mdに従って維持する。

## Purpose / Big Picture

「バベルの図書館」を女教皇枠に据え、残る21原型にも知識領域の架空アルカナを一枚ずつ割り当てた、最初の完全な22枚セットを作る。利用者はこのパックを選択して二段階抽選を行え、LLMは原型の中心的意味とカード固有の物語・助言を組み合わせて鑑定できる。

リポジトリルートで npm run validate:content を実行し、22原型、22カード、1領域、1パック、23画像アセットが検証済みと表示されれば動作を確認できる。

## Progress

- [x] (2026-07-19 18:10Z) 既存の22原型、バベルの図書館、Schema、manifest、検証CLIを確認した。
- [x] (2026-07-19 18:18Z) 知識領域とパックのJSON Schemaおよび実データを追加した。
- [x] (2026-07-19 18:24Z) 女教皇を除く21原型の架空アルカナJSONを追加し、バベルの図書館を同じ領域・パックへ移行した。
- [x] (2026-07-19 18:28Z) 全カードとパックカバーの画像アセット予約を台帳へ追加した。
- [x] (2026-07-19 18:33Z) manifestと検証CLIを領域・パック・完全セット検証へ拡張した。
- [x] (2026-07-19 18:38Z) 全検証を実行し、READMEと本ExecPlanへ結果を反映した。

## Surprises & Discoveries

- Observation: 既存manifestは原型、カード、アセットのみを索引化し、カードのdomainIdsとpackIdsは参照先の存在を検証していない。
  Evidence: tools/validate-content.mjsはcard.archetypeIdとvisualのアセット参照を検証するが、domainIdsとpackIdsは検証対象外だった。

- Observation: 既存のカードSchemaは領域・パックIDを保持できたため、カード形式の破壊的変更なしで正規参照へ移行できた。
  Evidence: バベルの図書館はschemaVersion 1.0.0を維持し、contentVersionだけを2へ上げてdomainIdsとpackIdsを差し替えられた。

- Observation: 新しい領域・パック検証と22枚のカード追加に、新しいnpm依存関係は不要だった。
  Evidence: 既存のAjvとajv-formatsだけで7種類のSchemaをコンパイルし、全参照検証が終了コード0で完了した。

## Decision Log

- Decision: 知識領域とパックをカードとは別の正規JSONとして追加する。
  Rationale: 領域の解釈方針と、販売・配布単位になり得るパックの収録内容を独立して差し替えられるようにするため。
  Date/Author: 2026-07-19 / Codex

- Decision: 第一集はone-per-major-archetypeポリシーで22原型を各一枚ずつ収録する。
  Rationale: 「ワンセット」の境界を機械検証でき、欠落・重複した原型を公開前に検出できるため。
  Date/Author: 2026-07-19 / Codex

- Decision: 全カード画像とパックカバーはplannedとしてローカルWebPとリモート原寸PNGの両方を予約する。
  Rationale: 画像生成・検品は別工程としつつ、Sites軽量版と将来のオブジェクトストレージ配信の契約を先に固定するため。
  Date/Author: 2026-07-19 / Codex

## Outcomes & Retrospective

`knowledge`領域と`knowledge-arcana-vol-1`パックを追加し、「バベルの図書館」を女教皇枠として残したまま、残る21原型へ知識領域の架空アルカナを一枚ずつ作成した。各カードは固有の象徴、矛盾、物語、正位置・逆位置、仕事・関係・創作・自己の解釈を持ち、原型の必須テーマを少なくとも一つ継承している。

manifestは1.1.0へ更新し、領域とパックを正式な索引対象にした。検証CLIは、カードから領域・パックへの参照、パックとカードの相互参照、カバー種別、収録件数、原型の欠落・重複まで検出する。`npm run validate:content`は22原型、22カード、1領域、1パック、23アセットを検証して終了コード0で完了した。

カード画像22点とパックカバー1点は配置契約だけを予約し、すべて`planned`である。次工程は画像生成、人手検品、ローカルWebPの配置、リモート原寸PNGのアップロード後にアセットを`available`へ進めることである。

## Context and Orientation

packages/content/archetypesには0から21の22原型があり、各原型のsemanticAnchors.requiredThemeIdsがカード側で継承すべき中心テーマを示す。packages/content/cardsには架空アルカナを置き、visual.primaryAssetIdからpackages/content/assets/assets.jsonの画像へ解決する。

今回追加するpackages/content/domains/knowledge.jsonは知識領域共通の解釈・生成・ビジュアル方針を保持する。packages/content/packs/knowledge-arcana-vol-1.jsonは第一集の収録カードID、アクセス方針、構成ポリシーを保持する。packages/content/manifest.jsonは全コンテンツの入口である。

## Plan of Work

最初にdomain.schema.jsonとpack.schema.jsonを追加し、知識領域と第一集の設定を作成する。次に各原型の中心的意味を知識の生成、保存、分類、伝達、誤読、改訂、公開といった営みへ写像した21枚を追加し、既存のバベルの図書館を第一集へ所属させる。

その後、各カードのprimaryAssetIdとパックカバーをassets.jsonへplannedとして登録する。manifestへdomainsとpacksの索引を加え、検証CLIで参照整合性、ファイル一覧、件数、パックのカード収録、22原型一巡を検証する。最後にREADMEを新しい構成と検証結果へ更新する。

## Concrete Steps

作業ディレクトリをリポジトリルートとし、次を実行する。

    npm run validate:content

成功時は次の要旨を含む出力になる。

    Validated 22 archetypes, 22 cards, 1 domain, 1 pack, and 23 assets.
    Content validation passed.

カードIDと原型の対応を独立して確認する場合は、次を実行する。

    jq -r '.id + "\t" + .archetypeId' packages/content/cards/*.json

## Validation and Acceptance

npm run validate:contentが終了コード0で完了することを必須とする。manifestの件数と実ファイルが一致し、すべてのcard.domainIdsとcard.packIdsが存在すること、pack.cardIdsが実在するカードだけを指すこと、one-per-major-archetypeのパックが正確に22枚かつ原型重複なしであることを検証する。

人が確認する受け入れ条件は、女教皇が引き続きバベルの図書館であること、ほかの21原型が知識領域の固有象徴を持つこと、正位置・逆位置と仕事・関係・創作・自己の助言が各カード固有であること、画像実体がなくても将来のローカル・リモート配置先が予約されていることである。

## Idempotence and Recovery

npm run validate:contentはコンテンツを書き換えず繰り返し実行できる。カードとパックはdraft、画像はplannedなので、この変更だけでは未検品コンテンツが公開対象にならない。検証に失敗した場合は表示されたファイルまたは参照IDを修正し再実行する。

## Artifacts and Notes

最終検証では次の出力を得た。

    > infinity-arcana@0.1.0 validate:content
    > node tools/validate-content.mjs

    Validated 22 archetypes, 22 cards, 1 domain, 1 pack, and 23 assets.
    Content validation passed.

`knowledge-arcana-vol-1.json`の`cardIds`は22件で、検証CLIが各カードの`archetypeId`を集合化し、22原型が一度ずつ含まれることを確認した。

Revision note (2026-07-19): 実装、文書更新、最終検証の完了を反映し、進捗、発見事項、成果、検証証跡を更新した。

## Interfaces and Dependencies

domain.schema.jsonとpack.schema.jsonはJSON Schema Draft 2020-12に準拠し、既存のshared.schema.jsonを参照する。tools/validate-content.mjsは既存のAjv依存だけで検証し、新しい実行時依存を追加しない。

アプリケーションはmanifestのdomainsとpacksを読み込み、ユーザーが領域またはパックを選択した後、pack.cardIdsを候補集合として利用できる。将来の抽選ポリシーはpackの構成から独立して差し替える。
