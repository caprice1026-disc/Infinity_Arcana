# 天体領域アルカナ第一集を画像付きで追加する

このExecPlanはリポジトリ直下のPLANS.mdに従い、Progress、Surprises & Discoveries、Decision Log、Outcomes & Retrospectiveを作業中に更新する。

## Purpose / Big Picture

天体をテーマにした22枚の新しいセットを、既存の知識領域セットと共存させる。各カードは大アルカナの異なる原型を継承し、固有の物語、正位置・逆位置、仕事・関係・創作・自己への助言、生成したイラストを持つ。利用者はSites-liteで新しいカードを引き、画像と意味を確認できる。ユーザーが指定したGitHubのmainへ反映し、リモートのコミットを確認するところまでを完了条件とする。

## Progress

- [x] (2026-09-22) 既存22枚、テンプレート、Schema、画像台帳、検証CLIを確認した。
- [x] (2026-09-22) 天体領域、22枚の意味、パックを作成した。
- [x] (2026-09-22) imagegen組み込みツールで22枚と共通裏面を生成・検品し、PNGとWebPを保存した。
- [x] (2026-09-22) 台帳、manifest、README、既存セット件数に依存する検証を更新した。
- [x] (2026-09-22) 構造・意味・画像・抽選・ブラウザ表示を検証した。
- [x] (2026-09-22) 実装コミット856f417をmainへプッシュし、git ls-remoteで同じSHAを確認した。

## Surprises & Discoveries

既存の画像ビルダーは全カードのPNGをcards/babel-libraryから探すため、新セットを別ディレクトリに置くと既存コマンドが失敗する。パックのcardIdsで処理対象を限定する小さな変更と、複数パックを含む検証が必要になる。

既存テストの一部は全カード22枚を前提としている。知識セットのテストはパックで絞り、全体の期待件数は44枚へ更新する。

Sites-liteのrenderDrawはlocalizedContent直下にmeaningsがあると仮定しており、実データのja-JP階層と一致していなかった。ブラウザの抽選でTypeErrorを再現し、既存localized関数を通して意味を参照する一箇所の修正で解消した。再確認時は古いJavaScriptがブラウザキャッシュに残ったため、同じローカルサーバーのlocalhost側で新規に読み込んで確認した。

WindowsサンドボックスではNodeの子プロセスとPythonの一時領域に権限エラーが発生した。同じコマンドを通常権限で再実行し、コード変更なしで全テストが通過した。

## Decision Log

2026-09-22 / Codex: 既存と同じone-per-major-archetypeの22枚を一組とする。天体領域IDはcelestial、パックIDはcelestial-arcana-vol-1とする。元の22枚は変更しない。

2026-09-22 / Codex: 既存の金・紺・三日月のフレームを入力画像として使い、中央絵、上部番号、下部英語名を組み込みimagegenで生成する。科学説明用画像ではなく架空の象徴画として制作し、天体が人生の結果を決定するとは記述しない。

2026-09-22 / Codex: 検証済みカードと画像をavailable、領域・パックを既存と同じdraftにする。人手承認の記録やpublished状態を自動作成しない。GitHubへの追加はユーザーの明示依頼に基づく。

2026-09-22 / Codex: 既存画像ビルダーにpackIdと入力ディレクトリ指定を追加し、処理対象をパックのcardIdsで限定した。別の画像生成・変換基盤は追加しない。ブラウザで新セットを表示できることが完了条件のため、再現した意味の参照不具合も修正した。

## Outcomes & Retrospective

天体領域の22枚と共通裏面を制作し、1024×1536の原寸PNG23点と配信用WebP23点を保存した。パックカバーは共通裏面を再利用する。22枚に固有の象徴、矛盾、物語、正逆の意味・助言・警告、四分野の解釈を収録し、全カードで原型の必須テーマを継承した。

構造検証は22原型・44カード・2領域・2パック・3スプレッド・48アセットで成功。Python 21件、JavaScript 3件が通過し、品質検証はエラー0件、既存知識セットの文言に関する警告2件だった。新セットの警告、名前・キーワード重複候補、画像ハッシュ不一致はない。

Sites-liteでは実際の抽選後に「双星の誓約」の正位置、「銀河の環冠」と「軌道を持たない彗星」の逆位置の画像・日本語本文を確認した。知識セットの既存カードも表示できた。Geminiの外部API呼び出しは今回の検証対象に含めていない。

実装コミット856f4174d93d3f155f381c976c5fac1c28d9e1deをGitHubのcaprice1026-disc/Infinity_Arcanaのmainへプッシュし、リモートSHAの一致を確認した。この完了記録は続く文書コミットに含める。

## Context and Orientation

packages/content/archetypes/*.jsonのsemanticAnchors.requiredThemeIdsが継承すべき意味を指定する。cards/*.jsonが各カード、domains/*.jsonが領域方針、packs/*.jsonがセット構成、manifest.jsonが読み込み対象を保持する。assets/assets.jsonはカードの画像IDから実ファイルへの対応表であり、SHA-256は画像が台帳通りであることを確認するハッシュ値である。

cards/template/infinity-arcana-card-frame-wide-nameplate-v2.pngが共通フレーム。新しい原寸画像はcards/celestial-arcana、配信画像はapps/sites-lite/public/assets/cards/<card-id>/front.webpへ保存する。共通裏面とパック表紙は同じ天体装飾画を使い、別用途のアセットIDを登録する。

## Plan of Work

第一段階では天体の固有象徴を22原型へ割り当て、日本語のカード、領域、パックJSONを作る。正位置と逆位置の違い、行動に移せる助言、仕事など四分野の解釈を各カードに含める。

第二段階ではテンプレートから各カードを個別生成する。完全なフレーム、正しい番号と英語名、内容に合う中心的象徴を目視確認する。生成時のプロンプトをcards/celestial-arcana/image-prompts.jsonへ保存し、画像をWebPへ変換して寸法・バイト数・SHA-256を台帳へ登録する。PNGはGit内の原本として保存する。

第三段階ではmanifest、README、画像ビルダーの対象範囲とテストを更新する。構造・品質・既存回帰検証とSites-liteの画像・意味表示を確認し、mainへ通常のpushを行う。

## Concrete Steps

作業ディレクトリはC:\Users\Hodaka\Downloads\div\Infinity_Arcana。既存のPython、Node、ffmpegを使用し、依存を増やさない。

    npm.cmd run validate:content
    python -m unittest discover -s tests -v
    node --test test/build-babel-library-assets.test.mjs apps/sites-lite/test/engine.test.mjs
    npm.cmd run content:quality
    npm.cmd run sites:build
    git diff --check

表面画像はnpm.cmd run assets:build:celestialで再生成できる。裏面変換とプロンプトの場所はcards/celestial-arcana/README.mdに記載した。生成は組み込みimagegenのみを使用し、CLI/APIへの切り替えは行っていない。

## Validation and Acceptance

構造検証は22原型、44カード、2領域、2パック、3スプレッド、48アセットを期待する。新パックは22原型が重複なく揃い、すべての表面と共通裏面が存在し、画像の寸法・ハッシュが一致する。正位置・逆位置と四分野の意味をすべて持つことを確認する。

Sites-liteをビルドしてローカルHTTPサーバーで起動し、天体カードの画像と正逆の意味を表示できることをブラウザで確認する。最後にgit ls-remote origin refs/heads/mainのSHAがローカルHEADと一致することを確認する。

## Idempotence and Recovery

生成成功画像を保存してから次へ進み、失敗した画像だけを再生成する。検証は繰り返し可能。既存画像やカードは上書きしない。pushが不明確に終わった場合は先にリモートSHAを確認し、force pushは行わない。

## Artifacts and Notes

画像生成にはimagegenスキルの組み込みツールを使った。プロンプトと原寸画像をcards/celestial-arcanaに同梱した。画像の番号、英語名、枠、中心的象徴を全23点で目視確認した。

## Interfaces and Dependencies

Schemaとアプリのコンテンツ契約は維持する。変換は既存ffmpeg、検証は既存AjvとPython標準ライブラリを使用する。

2026-09-22: 既存構成を確認して計画を作成した。

2026-09-22: 画像と意味の完成、回帰テスト、ブラウザ実測を反映した。抽選表示を妨げていた既存のロケール参照不具合の修正を記録した。

2026-09-22: GitHub mainへの実装コミットの反映を確認し、完了記録を追加した。
