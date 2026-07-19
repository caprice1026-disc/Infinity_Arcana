# Infinity Arcana content

このディレクトリは、アプリケーションから独立した公開コンテンツの正本です。`manifest.json`を入口として原型、架空アルカナ、画像アセット台帳を読み込みます。

## 画像の参照

カードJSONはファイルパスやURLを直接持たず、`visual.primaryAssetId`で`assets/assets.json`のアセットを参照します。アセットには用途別のvariantを複数登録できます。

- `local`：`assetRoots[].basePath`と相対`path`を結合して解決します。Sites軽量版へ同梱する画像に使用します。
- `remote-url`：公開HTTPS URLから取得します。
- `object-storage`：S3、R2、GCS、Azure Blobなどから取得します。`connectionId`はサーバー側設定を指し、認証情報をJSONへ保存しません。`access`が`signed`の場合はサーバー側で期限付きURLを発行します。

同じアセットにローカル表示用WebPと、リモート保存された原寸PNGを登録できます。カード定義は保存場所が変わっても変更しません。

## 状態

画像がまだ制作されていないアセットは`planned`として登録できます。`available`へ変更すると、検証処理がローカル画像の存在を確認します。カードも画像と人手レビューが完了するまでは`draft`のままにします。

## 検証

リポジトリルートで次を実行します。

```sh
npm install
npm run validate:content
```
