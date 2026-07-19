# Infinity Arcana（無限アルカナ）

既存タロットの大アルカナ22種を「原型」として、その意味を継承した架空アルカナを多数展開するWebアプリケーションです。

ユーザーが引くのは単なる「女教皇」ではありません。女教皇の原型から顕現した「バベルの図書館」のように、独自の名前、世界観、象徴、正位置・逆位置の意味を持つカードです。抽選後は、相談内容とカード設定をLLMが結び付けて鑑定します。

## 基本構造

```text
22の大アルカナ原型
└── 原型ごとの架空アルカナ
    ├── 固有の象徴・物語
    ├── 正位置・逆位置
    ├── 相談分野別の解釈
    └── 画像アセット参照
```

架空アルカナは原型の中心的意味を必ず継承します。表現、物語、助言はカード側で拡張できますが、原型の意味を否定する上書きは認めません。

大アルカナの番号はRider–Waite–Smith系の順序を採用し、「力」をVIII、「正義」をXIとしています。

## 知識領域アルカナ 第一集

最初の完全セットとして、書物、記録、目録、翻訳、注釈、地図、記憶を扱う[知識領域](packages/content/domains/knowledge.json)と、22原型を各1枚ずつ収録する[知識領域アルカナ 第一集](packages/content/packs/knowledge-arcana-vol-1.json)を追加しています。

パックは`compositionPolicy.type: one-per-major-archetype`を宣言し、検証処理が22枚、原型の欠落・重複、カード側との相互参照を確認します。現在はコンテンツと画像の検品前なので、領域、パック、全カードは`draft`、画像アセットは`planned`です。

### 収録カード

| 番号 | 原型 | 架空アルカナ |
|---:|---|---|
| 00 | 愚者 | [未記載の頁](packages/content/cards/unwritten-page.json) |
| 01 | 魔術師 | [万象の写字生](packages/content/cards/scribe-of-all-things.json) |
| 02 | 女教皇 | [バベルの図書館](packages/content/cards/babel-library.json) |
| 03 | 女帝 | [物語の果樹園](packages/content/cards/orchard-of-stories.json) |
| 04 | 皇帝 | [第一目録](packages/content/cards/first-catalogue.json) |
| 05 | 教皇 | [千年講堂](packages/content/cards/millennial-lecture-hall.json) |
| 06 | 恋人 | [双生の異本](packages/content/cards/twin-variant-texts.json) |
| 07 | 戦車 | [走る大書庫](packages/content/cards/roaming-grand-library.json) |
| 08 | 力 | [獣語の編纂者](packages/content/cards/compiler-of-beast-tongues.json) |
| 09 | 隠者 | [最後の注釈者](packages/content/cards/last-annotator.json) |
| 10 | 運命の輪 | [年代記が書き換わる夜](packages/content/cards/night-the-chronicle-rewrites.json) |
| 11 | 正義 | [証言の天秤](packages/content/cards/scales-of-testimony.json) |
| 12 | 吊るされた男 | [逆さの地図帳](packages/content/cards/inverted-atlas.json) |
| 13 | 死神 | [最後の改訂](packages/content/cards/final-revision.json) |
| 14 | 節制 | [二つのインク工房](packages/content/cards/workshop-of-two-inks.json) |
| 15 | 悪魔 | [引用の迷宮](packages/content/cards/labyrinth-of-citations.json) |
| 16 | 塔 | [崩落する書塔](packages/content/cards/collapsing-book-tower.json) |
| 17 | 星 | [失われた航路の星図](packages/content/cards/chart-of-the-lost-route.json) |
| 18 | 月 | [月光写本](packages/content/cards/moonlight-manuscript.json) |
| 19 | 太陽 | [正午の公開書庫](packages/content/cards/noon-open-archive.json) |
| 20 | 審判 | [再読の日](packages/content/cards/day-of-rereading.json) |
| 21 | 世界 | [円環百科全書](packages/content/cards/cyclical-encyclopedia.json) |

### 女教皇枠：バベルの図書館

女教皇の原型から派生した[バベルの図書館](packages/content/cards/babel-library.json)は、第一集の起点となったカードです。

| 項目 | 内容 |
|---|---|
| カードID | `babel-library` |
| 原型 | `high-priestess`（女教皇） |
| 顕現形態 | 場所 |
| 中心的象徴 | あらゆる文章を収め、無限に連なる六角形の書庫 |
| 中心的矛盾 | すべての答えが存在するが、目的の一冊を発見できる保証はない |
| 継承テーマ | 隠された知識、受容 |
| 現在の状態 | `draft` |

JSONには次の情報が含まれます。

- 原型、領域、パック、タグ
- 原型から継承した意味
- 固有の象徴、矛盾、物語
- 正位置・逆位置のキーワード、解釈、助言、警告
- 仕事、人間関係、創作、自己理解の分野別解釈
- 画像アセットID、代替テキスト、表示比率、焦点位置
- コンテンツ版と公開状態

カードの構造は[card.schema.json](packages/schemas/card.schema.json)で検証されます。

## 画像アセット

カードJSONへ画像パスやURLを直接埋め込まず、`visual.primaryAssetId`から[画像アセット台帳](packages/content/assets/assets.json)を参照します。

```text
babel-library.json
└── primaryAssetId: card-babel-library-front
    └── assets.json
        ├── display-local   → Sitesへ同梱するWebP
        └── original-remote → オブジェクトストレージ上の原寸PNG
```

画像の取得元は次の3方式に対応します。

| `source.type` | 用途 |
|---|---|
| `local` | 設定したアセットルートから相対パスで取得 |
| `remote-url` | 公開HTTPS URLから取得 |
| `object-storage` | S3、R2、GCS、Azure Blobなどから取得 |

オブジェクトストレージの認証情報はコンテンツJSONへ保存しません。`connectionId`を使ってサーバー側の環境設定へ解決します。`access: signed`の場合は、将来の通常版で期限付きURLを発行する想定です。

第一集のカード画像22点とパックカバー1点はまだ未制作なので、現在のアセット状態はすべて`planned`です。各アセットにはSites同梱用WebPと、S3互換ストレージ上の原寸PNGの配置先を予約しています。

## コンテンツ構成

```text
packages/
├── content/
│   ├── manifest.json
│   ├── archetypes/       # 大アルカナ22原型
│   ├── cards/            # 架空アルカナ
│   ├── domains/          # テーマ領域と解釈・生成方針
│   ├── packs/            # 収録カードと配布単位
│   └── assets/           # 画像アセット台帳
└── schemas/
    ├── shared.schema.json
    ├── archetype.schema.json
    ├── card.schema.json
    ├── domain.schema.json
    ├── pack.schema.json
    ├── asset-catalog.schema.json
    └── manifest.schema.json
```

アプリケーションは[manifest.json](packages/content/manifest.json)を入口として、公開対象の原型、カード、領域、パック、画像台帳を読み込みます。

## 検証

Node.jsを用意し、リポジトリルートで実行します。

```sh
npm ci
npm run validate:content
```

成功時の出力：

```text
Validated 22 archetypes, 22 cards, 1 domain, 1 pack, and 23 assets.
Content validation passed.
```

検証処理では以下を確認します。

- JSON Schemaへの適合
- 原型が0から21まで重複なく揃っていること
- manifestの件数とファイル一覧
- 架空アルカナが原型の必須テーマを継承していること
- カードから領域、パック、画像アセットへの参照
- パックとカードの相互参照、収録件数、原型の欠落・重複
- パックカバーとカード画像の種別
- 利用可能状態のローカル画像が実在すること

## コンテンツの状態

```text
draft
→ generated
→ automatically-validated
→ needs-review
→ approved
→ published
→ deprecated
```

公開済みにする前に、設定と画像の人手レビューを必須とします。

詳しい要件と設計は[無限アルカナ 共通エンジン 要件定義・基本設計書](infinite-arcana-requirements-design.md)を参照してください。
