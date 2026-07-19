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

## サンプルカード：バベルの図書館

最初の架空アルカナとして、女教皇の原型から派生した[バベルの図書館](packages/content/cards/babel-library.json)を収録しています。

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

バベルの図書館の画像はまだ未制作なので、現在のアセット状態は`planned`です。

## コンテンツ構成

```text
packages/
├── content/
│   ├── manifest.json
│   ├── archetypes/       # 大アルカナ22原型
│   ├── cards/            # 架空アルカナ
│   └── assets/           # 画像アセット台帳
└── schemas/
    ├── shared.schema.json
    ├── archetype.schema.json
    ├── card.schema.json
    ├── asset-catalog.schema.json
    └── manifest.schema.json
```

アプリケーションは[manifest.json](packages/content/manifest.json)を入口として、公開対象の原型、カード、画像台帳を読み込みます。

## 検証

Node.jsを用意し、リポジトリルートで実行します。

```sh
npm ci
npm run validate:content
```

成功時の出力：

```text
Validated 22 archetypes, 1 card, and 1 asset.
Content validation passed.
```

検証処理では以下を確認します。

- JSON Schemaへの適合
- 原型が0から21まで重複なく揃っていること
- manifestの件数とファイル一覧
- 架空アルカナが原型の必須テーマを継承していること
- カードから画像アセットへの参照
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
