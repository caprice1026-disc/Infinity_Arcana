# バベルの図書館カード画像をWebPとして配信パスへ配置する

このExecPlanは生きた文書である。作業中は `Progress`、`Surprises & Discoveries`、`Decision Log`、`Outcomes & Retrospective` を実態に合わせて更新する。リポジトリ直下の `PLANS.md` に従って維持する。

## Purpose / Big Picture

`cards/babel-library/` の22枚のPNGを、コンテンツ台帳が指定するWebPへ変換する。各カードJSONは画像パスを直接持たず、`visual.primaryAssetId` から `packages/content/assets/assets.json` のアセットを参照する。完了後はこの台帳のローカルパスである `apps/sites-lite/public/assets/cards/<カードID>/front.webp` に実体があり、台帳にはサイズとSHA-256が記録される。

利用者はリポジトリ直下で `npm.cmd run assets:build:babel-library` を実行して、PNGが更新された場合にも同じ配信用WebPを再生成できる。`npm.cmd run validate:content` はカードからアセット台帳を通じた参照と、availableになったローカルWebPの存在を検証する。

## Progress

- [x] (2026-07-20) カードJSON、アセット台帳、検証CLI、入力PNG 22枚を確認した。
- [x] (2026-07-20) `test/build-babel-library-assets.test.mjs` を追加し、実装モジュール不在による失敗を確認した。
- [x] (2026-07-20) 入力版名が `front-v1` と `front-cursive-v1` で混在する失敗を再現するテストを追加した。
- [x] (2026-07-20) `tools/build-babel-library-assets.mjs` とnpm scriptを実装し、テストを通した。
- [x] (2026-07-20) 22枚のPNGをWebPへ変換し、アセット台帳を更新した。
- [x] (2026-07-20) コンテンツ検証、WebPの寸法・サイズ・SHA-256・台帳パス照合を実行した。

## Surprises & Discoveries

- Observation: ImageMagickとcwebpは使用できないが、PATHに `ffmpeg` と `ffprobe` が存在した。
  Evidence: `Get-Command ffmpeg` は `C:\Users\Hodaka\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe` を返した。
- Observation: 22個のカード入力は版名が一律ではない。
  Evidence: `card-babel-library-front-cursive-v1.png` に対し、残りは `card-<slug>-front-v1.png` であった。
- Observation: PowerShellでは `npm.ps1` が実行ポリシーで拒否される。
  Evidence: `npm run ...` は `PSSecurityException`、`npm.cmd run ...` は正常に実行された。

## Decision Log

- Decision: Node.jsのCLIから既存の `ffmpeg` と `ffprobe` を起動する。
  Rationale: ネイティブnpm依存を増やさず、現在のWindows環境で実測を含む変換ができるため。
  Date/Author: 2026-07-20 / Codex
- Decision: 出力先は固定せず、`assets.json` の `assetRoots[].basePath` と既定variantの `source.path` を結合して決める。
  Rationale: カードと画像を結ぶ正式な契約はアセット台帳であり、台帳の変更にCLIを追随させるため。
  Date/Author: 2026-07-20 / Codex
- Decision: 入力PNGは `card-<slug>-front-*.png` に一意に一致するものを選ぶ。
  Rationale: 版名の差を受け入れながら、カードIDと画像の取り違えを検出するため。
  Date/Author: 2026-07-20 / Codex
- Decision: 変換後のカードfrontアセットを `available` にして、`byteSize` と `sha256` を記録する。
  Rationale: 既存のコンテンツ検証が台帳パスの実ファイル存在を確認でき、再現性も得られるため。
  Date/Author: 2026-07-20 / Codex

## Outcomes & Retrospective

22枚のPNGをすべて1024x1536のWebPに変換し、台帳指定の `apps/sites-lite/public/assets/cards/` 配下に配置した。`packages/content/assets/assets.json` はcatalogVersion 3となり、カードfrontの22アセットが `available` になった。各display-local variantには実測したファイルサイズとSHA-256が入っている。入力のないパック表紙は対象外のため `planned` のままである。

## Context and Orientation

`packages/content/cards/*.json` の `visual.primaryAssetId` は、`packages/content/assets/assets.json` の `assets[].id` を参照する。対象アセットの既定variantは `display-local` であり、その `source.rootId` を `assetRoots` から引き、`source.path` を結合することで配信用WebPの位置を解決する。今回の全カードではその位置が `apps/sites-lite/public/assets/cards/<slug>/front.webp` になる。

`tools/validate-content.mjs` はJSON Schemaと参照関係を検証する。アセットが `available` の場合、ローカルvariantの解決先が実在しなければ失敗する。したがって変換後のvalidation成功は、カードの画像ID、台帳、ファイル配置が接続していることを示す。

## Plan of Work

テストはNode.js標準の `node:test` を使い、一時リポジトリ内に最小のアセット台帳と入力PNGを作る。変換関数を呼び、台帳のパスにWebPが作られること、statusがavailableになること、サイズとハッシュが記録されることを確認する。実装前に対象モジュール不在で失敗し、次に固定のcursive版名では通常版名を受け入れられず失敗することを確認した。

CLIはアセット台帳から `kind: "card-front"` の既定ローカルWebP variantを集める。各アセットIDからPNG名の接頭辞を作り、入力ディレクトリに一致するPNGが一つだけ存在することを変換前に確認する。ffmpegで台帳が宣言する幅と高さへ変換し、ffprobeで生成寸法を検査する。成功後にファイルサイズとSHA-256を台帳に書き、statusをavailableに進める。再実行時にメタデータが同じなら台帳versionは増やさない。

## Concrete Steps

作業ディレクトリはリポジトリ直下である。

1. 変換CLIのテストを実行する。

    node --test test/build-babel-library-assets.test.mjs

2. 入力PNGを変換し、台帳を更新する。PowerShellでは実行ポリシーのため `npm.cmd` を使う。

    npm.cmd run assets:build:babel-library

3. コンテンツのSchema、参照、available画像の存在を検証する。

    npm.cmd run validate:content

4. 必要ならCLIを再実行する。同じ画像内容なら台帳のcatalogVersionとcontentVersionに余分な変更は出ない。

## Validation and Acceptance

受け入れ条件は以下である。

- `node --test test/build-babel-library-assets.test.mjs` が1件成功する。
- `npm.cmd run assets:build:babel-library` が22枚の変換を報告する。
- `npm.cmd run validate:content` が `Content validation passed.` を表示する。
- 全22個のカードfront WebPについて、ffprobeの寸法が台帳の1024x1536に一致し、実ファイルのサイズとSHA-256が台帳の `byteSize` と `sha256` に一致する。

実行結果は以下のとおりである。

    node --test test/build-babel-library-assets.test.mjs
    # tests 1
    # pass 1
    # fail 0

    npm.cmd run assets:build:babel-library
    Converted 22 Babel Library card PNGs to catalog WebP paths and updated the asset catalog.

    npm.cmd run validate:content
    Validated 22 archetypes, 22 cards, 1 domain, 1 pack, and 23 assets.
    Content validation passed.

    Verified 22 available card WebPs: dimensions, byte sizes, SHA-256 values, and catalog paths all match.

## Idempotence and Recovery

変換CLIは再実行可能である。すべての入力PNGを先に列挙して一意性を確認するため、入力不足や重複名があれば変換を開始せずに失敗する。ffmpegの途中失敗時は台帳更新前に停止するため、入力または環境を修正して同じコマンドを再実行すればよい。生成済みWebPはffmpegで上書きされる。

## Artifacts and Notes

主な変更ファイルは `tools/build-babel-library-assets.mjs`、`test/build-babel-library-assets.test.mjs`、`package.json`、`packages/content/assets/assets.json`、および生成先の `apps/sites-lite/public/assets/cards/` である。

## Interfaces and Dependencies

`tools/build-babel-library-assets.mjs` は次の関数をexportする。

    export async function buildBabelLibraryAssets(options)

`options` には `repositoryRoot`、`sourceDirectory`、`contentDirectory`、`ffmpegPath`、`ffprobePath` を指定できる。省略時はリポジトリの既定ディレクトリとPATH上の `ffmpeg` / `ffprobe` を使う。CLI実行時は変換件数を標準出力へ表示し、台帳、入力、生成寸法の不整合で終了コード1になる。

Revision note (2026-07-20): 実画像配置とアセット台帳更新を実施し、入力版名の不統一へ対応した。実変換と全検証の結果を反映した。
