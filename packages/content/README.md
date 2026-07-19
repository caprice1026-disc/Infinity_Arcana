# Infinity Arcana content

このディレクトリは、アプリケーションから独立した公開コンテンツの正本です。`manifest.json`を入口として原型、架空アルカナ、領域、パック、画像アセット台帳を読み込みます。

## 領域とパック

`domains/`は複数パックで共有するテーマの範囲、解釈方針、生成指針、ビジュアル方針を保持します。`packs/`は収録カード、アクセス方針、セット構成を保持し、抽選候補や将来の配布・販売単位として利用できます。

`knowledge-arcana-vol-1`は、`knowledge`領域から22原型を各1枚ずつ収録する最初の完全セットです。`one-per-major-archetype`構成は検証CLIが件数、原型の欠落・重複、カードとの相互参照まで確認します。

## 画像の参照

カードJSONはファイルパスやURLを直接持たず、`visual.primaryAssetId`で`assets/assets.json`のアセットを参照します。アセットには用途別のvariantを複数登録できます。

- `local`：`assetRoots[].basePath`と相対`path`を結合して解決します。Sites軽量版へ同梱する画像に使用します。
- `remote-url`：公開HTTPS URLから取得します。
- `object-storage`：S3、R2、GCS、Azure Blobなどから取得します。`connectionId`はサーバー側設定を指し、認証情報をJSONへ保存しません。`access`が`signed`の場合はサーバー側で期限付きURLを発行します。

同じアセットにローカル表示用WebPと、リモート保存された原寸PNGを登録できます。カード定義は保存場所が変わっても変更しません。

## 状態

画像がまだ制作されていないアセットは`planned`として登録できます。`available`へ変更すると、検証処理がローカル画像の存在を確認します。カード、領域、パックも画像と人手レビューが完了するまでは`draft`のままにします。

## 検証

リポジトリルートで次を実行します。

```sh
npm install
npm run validate:content
```
